from urllib.parse import urlsplit, urlunsplit

import httpx

from app.config import settings
from app.models import NormalizedLinkedInPost, ReactionSample, SuggestionRequest


class ApifyLinkedInDiscoveryAdapter:
    """Fetch and normalize LinkedIn posts plus engagement enrichment."""

    BASE_URL = "https://api.apify.com/v2/acts"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client
        self.last_warning: str | None = None

    async def discover(
        self, request: SuggestionRequest
    ) -> list[NormalizedLinkedInPost]:
        self.last_warning = None
        if not settings.apify_api_token:
            raise RuntimeError(
                "APIFY_API_TOKEN is required for live LinkedIn discovery."
            )

        if self._client is not None:
            return await self._discover_with_client(self._client, request)

        async with httpx.AsyncClient(timeout=120.0) as client:
            return await self._discover_with_client(client, request)

    @staticmethod
    def normalize_posts(raw_posts: list[dict]) -> list[NormalizedLinkedInPost]:
        posts: list[NormalizedLinkedInPost] = []

        for item in raw_posts:
            post_url = item.get("post_url") or ""
            if not post_url:
                continue

            author = item.get("author") or {}
            stats = item.get("stats") or {}
            reaction_breakdown = stats.get("reactions") or []
            text = (item.get("text") or "").strip()

            posts.append(
                NormalizedLinkedInPost(
                    activity_id=str(
                        item.get("activity_id") or item.get("full_urn") or ""
                    ),
                    post_url=post_url,
                    author_name=(author.get("name") or "").strip() or "Unknown author",
                    author_headline=(author.get("headline") or "").strip(),
                    author_profile_url=(author.get("profile_url") or "").strip(),
                    preview=_preview_text(text),
                    full_text=text,
                    hashtags=[
                        tag
                        for tag in item.get("hashtags") or []
                        if isinstance(tag, str)
                    ],
                    total_reactions=_to_int(
                        stats.get("total_reactions"),
                        fallback=sum(
                            _to_int(reaction.get("count"))
                            for reaction in reaction_breakdown
                            if isinstance(reaction, dict)
                        ),
                    ),
                    total_comments=_to_int(stats.get("comments")),
                    total_shares=_to_int(stats.get("shares")),
                    reaction_types=[
                        reaction.get("type", "")
                        for reaction in reaction_breakdown
                        if isinstance(reaction, dict) and reaction.get("type")
                    ],
                    published_timestamp=_to_int(
                        (item.get("posted_at") or {}).get("timestamp")
                    ),
                    search_query=str(item.get("search_input") or ""),
                )
            )

        return posts

    async def _discover_with_client(
        self,
        client: httpx.AsyncClient,
        request: SuggestionRequest,
    ) -> list[NormalizedLinkedInPost]:
        raw_posts = await self._run_actor(
            client,
            actor_id=settings.apify_posts_actor_id,
            payload={
                "keyword": _build_search_keyword(request),
                "sort_type": "relevance",
                "total_posts": max(settings.reaction_enrichment_count, 3),
            },
        )
        posts = self.normalize_posts(raw_posts)

        if not posts:
            return []

        posts_to_enrich = posts[: settings.reaction_enrichment_count]
        try:
            raw_reactions = await self._run_actor(
                client,
                actor_id=settings.apify_reactions_actor_id,
                payload={
                    "posts": [post.post_url for post in posts_to_enrich],
                    "maxItems": settings.max_reactions_per_post,
                    "profileScraperMode": "short",
                },
            )
        except httpx.HTTPError:
            self.last_warning = (
                "Some engagement signals were unavailable. You can still use these "
                "ranked posts and rerun for a fuller result."
            )
            return posts
        return _attach_reactions(posts, raw_reactions)

    async def _run_actor(
        self,
        client: httpx.AsyncClient,
        actor_id: str,
        payload: dict,
    ) -> list[dict]:
        actor_path = actor_id.replace("/", "~")
        response = await client.post(
            f"{self.BASE_URL}/{actor_path}/run-sync-get-dataset-items",
            params={"token": settings.apify_api_token},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        return []


def _build_search_keyword(request: SuggestionRequest) -> str:
    parts = [f'"{request.topic.strip()}"']
    parts.extend(keyword.strip() for keyword in request.keywords if keyword.strip())
    parts.append(request.persona.strip())
    return " ".join(parts)


def _attach_reactions(
    posts: list[NormalizedLinkedInPost],
    raw_reactions: list[dict],
) -> list[NormalizedLinkedInPost]:
    reactions_by_post: dict[str, list[ReactionSample]] = {}

    for item in raw_reactions:
        actor = item.get("actor") or {}
        query = item.get("query") or {}
        reaction_post_url = _canonical_post_url(str(query.get("post") or ""))
        if not reaction_post_url:
            continue

        reactions_by_post.setdefault(reaction_post_url, []).append(
            ReactionSample(
                reactor_name=(actor.get("name") or "").strip() or "Unknown reactor",
                reactor_headline=(actor.get("position") or "").strip(),
                reactor_profile_url=(actor.get("linkedinUrl") or "").strip(),
                reaction_type=str(item.get("reactionType") or ""),
            )
        )

    enriched: list[NormalizedLinkedInPost] = []
    for post in posts:
        enriched.append(
            post.model_copy(
                update={
                    "reaction_samples": reactions_by_post.get(
                        _canonical_post_url(post.post_url),
                        [],
                    )
                }
            )
        )

    return enriched


def _canonical_post_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _preview_text(text: str, limit: int = 280) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _to_int(value: object, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback
