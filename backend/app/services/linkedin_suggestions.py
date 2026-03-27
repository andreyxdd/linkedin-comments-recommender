from app.models import (
    NormalizedLinkedInPost,
    PostEngagement,
    RankedPost,
    SuggestedComment,
    SuggestionRequest,
    SuggestionResult,
)


def build_suggestion_result(
    request: SuggestionRequest,
    posts: list[NormalizedLinkedInPost],
) -> SuggestionResult:
    """Convert live discovered posts into the public API result contract."""
    topic = request.topic.strip()
    persona = request.persona.strip()
    keywords = [keyword.strip() for keyword in request.keywords if keyword.strip()]
    ranked_records = posts[:3]
    if not ranked_records:
        raise RuntimeError("No LinkedIn posts were discovered for this request.")

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
            suggested_comments=_build_mock_comments(request, post, index),
        )
        for index, post in enumerate(ranked_records, start=1)
    ]

    keyword_summary = ", ".join(keywords)
    return SuggestionResult(
        posts=ranked_posts,
        partial=len(ranked_posts) < 3,
        request_summary=(
            f"{persona} exploring {topic} with keywords: {keyword_summary}."
        ),
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


def _build_mock_comments(
    request: SuggestionRequest,
    post: NormalizedLinkedInPost,
    rank: int,
) -> list[SuggestedComment]:
    topic = request.topic.strip()
    first_keyword = next(
        (keyword for keyword in request.keywords if keyword.strip()), topic
    )
    voice = _voice_descriptor(request)

    return [
        SuggestedComment(
            id=f"rank-{rank}-comment-1",
            text=(
                f"Strong point. The link between {topic} and {first_keyword} feels "
                "especially practical here, not just conceptually clean."
            ),
        ),
        SuggestedComment(
            id=f"rank-{rank}-comment-2",
            text=(
                f"This is a {voice} framing of the problem. I also like how the post "
                f"stays grounded in execution instead of treating {topic} like hype."
            ),
        ),
    ]


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
