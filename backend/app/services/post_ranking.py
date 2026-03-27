import re

from app.models import NormalizedLinkedInPost, SuggestionRequest


def rank_posts(
    request: SuggestionRequest,
    posts: list[NormalizedLinkedInPost],
) -> list[NormalizedLinkedInPost]:
    return sorted(
        posts,
        key=lambda post: (
            _relevance_score(request, post),
            _engagement_score(post),
            post.published_timestamp,
        ),
        reverse=True,
    )


def _relevance_score(request: SuggestionRequest, post: NormalizedLinkedInPost) -> float:
    searchable_text = _normalize_text(
        " ".join(
            [
                post.full_text,
                post.author_headline,
                " ".join(post.hashtags),
            ]
        )
    )
    score = 0.0

    topic = _normalize_text(request.topic)
    if topic and topic in searchable_text:
        score += 10.0

    persona = _normalize_text(request.persona)
    if persona and persona in searchable_text:
        score += 3.0

    for keyword in request.keywords:
        normalized_keyword = _normalize_text(keyword)
        if normalized_keyword and normalized_keyword in searchable_text:
            score += 5.0

    for token in _tokenize(request.topic):
        if token in searchable_text:
            score += 1.5

    for keyword in request.keywords:
        for token in _tokenize(keyword):
            if token in searchable_text:
                score += 1.0

    return score


def _engagement_score(post: NormalizedLinkedInPost) -> int:
    return (
        post.total_reactions
        + (post.total_comments * 4)
        + (post.total_shares * 6)
        + len(post.reaction_samples)
    )


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2]
