from app.models import (
    PostEngagement,
    RankedPost,
    SuggestedComment,
    SuggestionRequest,
    SuggestionResult,
)


def build_mock_suggestion_result(request: SuggestionRequest) -> SuggestionResult:
    """Return deterministic ranked post suggestions for the MVP demo flow."""
    topic = request.topic.strip()
    persona = request.persona.strip()
    keywords = [keyword.strip() for keyword in request.keywords if keyword.strip()]
    primary_keyword = keywords[0] if keywords else topic.lower()
    secondary_keyword = keywords[1] if len(keywords) > 1 else "thoughtful engagement"
    voice = _voice_descriptor(request)

    posts = [
        RankedPost(
            rank=1,
            author="Maya Chen",
            author_headline="B2B SaaS founder sharing weekly GTM notes",
            post_url="https://www.linkedin.com/posts/maya-chen-founder_gtm-playbook",
            preview=(
                f"We stopped treating {topic} like a feature checklist and started "
                f"treating it like a distribution wedge. The biggest unlock came "
                f"from tying every launch to {primary_keyword} conversations."
            ),
            rationale=(
                f"Strong match for a {persona.lower()} because it directly connects "
                f"{topic} to practical growth lessons and already attracts "
                f"discussion around {primary_keyword}."
            ),
            engagement=PostEngagement(reactions=186, comments=34),
            suggested_comments=[
                SuggestedComment(
                    id="rank-1-comment-1",
                    text=(
                        "Sharp framing. "
                        f"The shift from feature talk to {primary_keyword} "
                        f"conversations is exactly where {topic} starts to compound. "
                        "I also like how concrete the lesson feels without turning "
                        "into fluff."
                    ),
                ),
                SuggestedComment(
                    id="rank-1-comment-2",
                    text=(
                        f"This is a {voice} way to explain why distribution usually "
                        "beats novelty. "
                        f"Too many teams discuss {topic} in isolation instead of "
                        "tying it to the audience tension."
                    ),
                ),
            ],
        ),
        RankedPost(
            rank=2,
            author="Jordan Alvarez",
            author_headline="Operator writing about modern revenue systems",
            post_url="https://www.linkedin.com/posts/jordan-alvarez_revenue-systems-ops",
            preview=(
                f"A lot of teams say they care about {topic}, but their workflow still "
                f"creates bottlenecks. The real win is tightening the feedback loop "
                f"between experiments, sales calls, and {secondary_keyword}."
            ),
            rationale=(
                f"Relevant because it pairs strategic thinking with operating detail, "
                f"which gives a {persona.lower()} room to add credibility "
                "instead of generic praise."
            ),
            engagement=PostEngagement(reactions=141, comments=19),
            suggested_comments=[
                SuggestedComment(
                    id="rank-2-comment-1",
                    text=(
                        "Completely agree on the feedback-loop point. "
                        f"{topic} only becomes useful when the learning cycle "
                        "is tight enough to change decisions, not just slides."
                    ),
                ),
                SuggestedComment(
                    id="rank-2-comment-2",
                    text=(
                        f"What stands out here is the emphasis on execution hygiene. "
                        "The teams that connect "
                        f"{secondary_keyword} back to real customer signals "
                        "usually move faster."
                    ),
                ),
            ],
        ),
        RankedPost(
            rank=3,
            author="Priya Natarajan",
            author_headline="Advisor on product positioning and category narrative",
            post_url="https://www.linkedin.com/posts/priya-natarajan_positioning-category-story",
            preview=(
                f"If your take on {topic} sounds interchangeable, the market "
                "will treat it that way. "
                "A better approach is to anchor your POV in a tension the "
                "audience already feels every week."
            ),
            rationale=(
                f"Selected for explainable relevance: high alignment with {topic}, "
                "moderate engagement, and clear language that invites a "
                "nuanced comment."
            ),
            engagement=PostEngagement(reactions=118, comments=17),
            suggested_comments=[
                SuggestedComment(
                    id="rank-3-comment-1",
                    text=(
                        "That tension test is a useful filter. "
                        f"A lot of messaging around {topic} sounds polished, "
                        "but it still misses the discomfort people are actually "
                        "trying to resolve."
                    ),
                ),
                SuggestedComment(
                    id="rank-3-comment-2",
                    text=(
                        "Well said. The strongest positioning usually gives "
                        "people language for a problem they already feel, "
                        "which is why this framing lands more cleanly than "
                        "another abstract trend post."
                    ),
                ),
            ],
        ),
    ]

    keyword_summary = ", ".join(keywords)
    return SuggestionResult(
        posts=posts,
        partial=False,
        request_summary=(
            f"{persona} exploring {topic} with keywords: {keyword_summary}."
        ),
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
