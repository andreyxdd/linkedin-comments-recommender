import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.models import (
    NormalizedLinkedInPost,
    PostEngagement,
    RankedPost,
    SuggestedComment,
    SuggestionRequest,
    SuggestionResult,
)
from app.services.llm import get_generation_model

logger = logging.getLogger(__name__)


async def build_suggestion_result(
    request: SuggestionRequest,
    posts: list[NormalizedLinkedInPost],
    discovery_warning: str | None = None,
) -> SuggestionResult:
    """Convert live discovered posts into the public API result contract."""
    topic = request.topic.strip()
    persona = request.persona.strip()
    keywords = [keyword.strip() for keyword in request.keywords if keyword.strip()]
    ranked_records = posts[:3]
    if not ranked_records:
        raise RuntimeError("No LinkedIn posts were discovered for this request.")

    generated_comments, fallback_count = await _generate_comments(
        request,
        ranked_records,
    )
    ranked_posts = [
        RankedPost(
            rank=index,
            author=post.author_name,
            author_headline=post.author_headline,
            post_url=post.post_url,
            preview=post.preview,
            rationale=_build_rationale(request, post),
            engagement=PostEngagement(
                reactions=post.total_reactions,
                comments=post.total_comments,
            ),
            suggested_comments=generated_comments[index - 1],
        )
        for index, post in enumerate(ranked_records, start=1)
    ]

    keyword_summary = ", ".join(keywords)
    is_partial = len(ranked_posts) < 3 or fallback_count > 0 or bool(discovery_warning)
    recovery_message = _recovery_message(
        discovery_warning=discovery_warning,
        fallback_count=fallback_count,
        ranked_post_count=len(ranked_posts),
    )

    return SuggestionResult(
        posts=ranked_posts,
        partial=is_partial,
        request_summary=(
            f"{persona} exploring {topic} with keywords: {keyword_summary}."
        ),
        recovery_message=recovery_message,
    )


def _build_rationale(
    request: SuggestionRequest,
    post: NormalizedLinkedInPost,
) -> str:
    searchable = " ".join(
        [post.full_text, post.author_headline, *post.hashtags]
    ).lower()
    matched_keywords = [
        keyword for keyword in request.keywords if keyword.lower() in searchable
    ]
    match_summary = ", ".join(matched_keywords) or request.topic

    return (
        f"Ranked for strong relevance to {match_summary}, then backed by "
        f"{post.total_reactions} reactions and {post.total_comments} comments."
    )


async def _generate_comments(
    request: SuggestionRequest,
    posts: list[NormalizedLinkedInPost],
) -> tuple[list[list[SuggestedComment]], int]:
    try:
        generation_model = get_generation_model()
    except Exception as exc:  # pragma: no cover - defensive config fallback
        logger.warning("Falling back to deterministic comments: %s", exc)
        return (
            [
                _build_fallback_comments(request, post, rank)
                for rank, post in enumerate(posts, start=1)
            ],
            len(posts),
        )

    generated_comments: list[list[SuggestedComment]] = []
    fallback_count = 0
    for rank, post in enumerate(posts, start=1):
        messages = _comment_messages(request, post)

        try:
            generated_comments.append(
                await _generate_comments_for_post(generation_model, messages, rank)
            )
            continue
        except Exception as exc:
            logger.warning(
                "Falling back to deterministic comments for rank %s: %s",
                rank,
                exc,
            )
            generated_comments.append(_build_fallback_comments(request, post, rank))
            fallback_count += 1

    return generated_comments, fallback_count


def _recovery_message(
    discovery_warning: str | None,
    fallback_count: int,
    ranked_post_count: int,
) -> str | None:
    notes: list[str] = []

    if discovery_warning:
        notes.append(discovery_warning)

    if ranked_post_count < 3:
        notes.append(
            "We found fewer than three strong opportunities this run. "
            "Try broadening keywords and rerun."
        )

    if fallback_count > 0:
        notes.append(
            "Some comment drafts used a backup path. "
            "You can copy these now and rerun to refresh."
        )

    if not notes:
        return None

    return " ".join(notes)


async def _generate_comments_for_post(
    generation_model: Any,
    messages: list[SystemMessage | HumanMessage],
    rank: int,
) -> list[SuggestedComment]:
    response = await generation_model.ainvoke(messages)
    return _parse_generated_comments(rank, getattr(response, "content", ""))


def _comment_messages(
    request: SuggestionRequest,
    post: NormalizedLinkedInPost,
) -> list[SystemMessage | HumanMessage]:
    keywords = ", ".join(
        keyword.strip() for keyword in request.keywords if keyword.strip()
    )
    hashtags = ", ".join(post.hashtags) or "none"
    engagement_summary = (
        f"{post.total_reactions} reactions, {post.total_comments} comments"
    )

    return [
        SystemMessage(
            content=(
                "You write short LinkedIn comments for thoughtful professionals. "
                "Return strict JSON with exactly one key named 'comments' whose "
                "value is an array of exactly two strings. Each comment must be 1-2 "
                "sentences, concrete, human-sounding, and ready to paste as-is. "
                "Do not use emojis, hashtags, quotation marks around the full "
                "comment, or generic praise with no substance."
            )
        ),
        HumanMessage(
            content=(
                f"Persona: {request.persona.strip()}\n"
                f"Topic: {request.topic.strip()}\n"
                f"Keywords: {keywords}\n"
                f"Tone guidance: {_tone_guidance(request)}\n"
                f"Post author: {post.author_name}\n"
                f"Author headline: {post.author_headline or 'N/A'}\n"
                f"Post preview: {post.preview}\n"
                f"Post detail: {post.full_text[:900]}\n"
                f"Hashtags: {hashtags}\n"
                f"Engagement: {engagement_summary}\n"
                "Write two distinct comments. The first should validate a specific "
                "idea from the post. The second should add a thoughtful extension, "
                "implication, or respectful angle."
            )
        ),
    ]


def _parse_generated_comments(
    rank: int,
    content: Any,
) -> list[SuggestedComment]:
    payload_text = _content_to_text(content)
    payload = _extract_json_payload(payload_text)
    cleaned_comments = _extract_comment_texts(payload)
    cleaned_comments = [comment for comment in cleaned_comments if comment]
    if len(cleaned_comments) < 2:
        raise ValueError("Comment payload must contain two non-empty comments.")

    return [
        SuggestedComment(id=f"rank-{rank}-comment-1", text=cleaned_comments[0]),
        SuggestedComment(id=f"rank-{rank}-comment-2", text=cleaned_comments[1]),
    ]


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
                continue
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                text_parts.append(block["text"])
        return "\n".join(text_parts)

    return str(content)


def _extract_json_payload(payload_text: str) -> Any:
    decoder = json.JSONDecoder()
    start_indexes = sorted(
        set(
            [
                *[match.start() for match in re.finditer(r"\{", payload_text)],
                *[match.start() for match in re.finditer(r"\[", payload_text)],
            ]
        )
    )
    for start_index in start_indexes:
        try:
            payload, _ = decoder.raw_decode(payload_text[start_index:])
            return payload
        except json.JSONDecodeError:
            continue

    raise ValueError("Comment generation did not return JSON.")


def _extract_comment_texts(payload: Any) -> list[str]:
    if isinstance(payload, list):
        return _extract_comment_texts_from_sequence(payload)

    if isinstance(payload, dict):
        for key in ("comments", "drafts", "suggestions", "items"):
            extracted = _extract_comment_texts_from_sequence(payload.get(key))
            if extracted:
                return extracted

    raise ValueError("Comment payload missing recognizable comment content.")


def _extract_comment_texts_from_sequence(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []

    extracted_comments: list[str] = []
    for item in items:
        if isinstance(item, str):
            extracted_comments.append(_normalize_comment_text(item))
            continue

        if not isinstance(item, dict):
            continue

        for key in ("text", "content", "comment", "draft"):
            value = item.get(key)
            if isinstance(value, str):
                extracted_comments.append(_normalize_comment_text(value))
                break

    return extracted_comments


def _normalize_comment_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return normalized.strip("\"' ")


def _build_fallback_comments(
    request: SuggestionRequest,
    post: NormalizedLinkedInPost,
    rank: int,
) -> list[SuggestedComment]:
    topic = request.topic.strip()
    focus = _comment_focus(request, post)
    preview_focus = _preview_focus(post)
    opener, follow_up = _comment_openings(request)

    return [
        SuggestedComment(
            id=f"rank-{rank}-comment-1",
            text=(
                f"{opener}. The point about {preview_focus} lands because it makes "
                f"{topic} feel concrete instead of abstract."
            ),
        ),
        SuggestedComment(
            id=f"rank-{rank}-comment-2",
            text=(
                f"{follow_up}. Bringing {focus} into the discussion keeps the "
                f"{topic} conversation grounded in execution."
            ),
        ),
    ]


def _comment_focus(
    request: SuggestionRequest,
    post: NormalizedLinkedInPost,
) -> str:
    searchable = " ".join(
        [post.full_text, post.author_headline, *post.hashtags]
    ).lower()
    matched_keyword = next(
        (keyword for keyword in request.keywords if keyword.lower() in searchable),
        "",
    )
    if matched_keyword:
        return matched_keyword
    if post.hashtags:
        return post.hashtags[0].lstrip("#")
    return request.topic.strip()


def _preview_focus(post: NormalizedLinkedInPost) -> str:
    excerpt = post.preview.split(".")[0].strip()
    return excerpt[:120].rstrip(",;:") or "the operating detail"


def _comment_openings(request: SuggestionRequest) -> tuple[str, str]:
    warm = request.tone.reserved_warm >= 60
    bold = request.tone.measured_bold >= 60
    casual = request.tone.professional_casual >= 60

    if warm and bold and casual:
        return (
            "Love this angle",
            "You framed this in a way that feels sharp but usable",
        )
    if warm and bold:
        return ("Strong take", "I like how directly you framed this")
    if warm and casual:
        return ("Really like this point", "The warm but practical framing works")
    if bold:
        return ("Sharp point", "The direct framing works")
    if casual:
        return ("Good take", "This feels practical without trying too hard")
    return ("Thoughtful point", "The measured framing works")


def _tone_guidance(request: SuggestionRequest) -> str:
    casual = request.tone.professional_casual
    warm = request.tone.reserved_warm
    bold = request.tone.measured_bold
    fresh = request.tone.conventional_fresh

    return (
        f"Professional-casual={casual}/100, reserved-warm={warm}/100, "
        f"measured-bold={bold}/100, conventional-fresh={fresh}/100. "
        f"Use a {_voice_descriptor(request)} voice."
    )


def _voice_descriptor(request: SuggestionRequest) -> str:
    warm = request.tone.reserved_warm >= 60
    bold = request.tone.measured_bold >= 60
    casual = request.tone.professional_casual >= 60

    if warm and bold and casual:
        return "warm, direct"
    if warm and bold:
        return "warm, confident"
    if bold:
        return "confident"
    if casual:
        return "relaxed"
    return "measured"
