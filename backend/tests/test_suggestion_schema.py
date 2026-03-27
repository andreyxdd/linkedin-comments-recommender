import pytest
from pydantic import ValidationError

from app.models import PostEngagement, RankedPost, SuggestedComment


def _base_ranked_post_payload() -> dict:
    return {
        "rank": 1,
        "author": "Test Author",
        "author_headline": "Test Headline",
        "post_url": "https://www.linkedin.com/posts/test-post",
        "preview": "Preview text",
        "full_text": "Full post text",
        "rationale": "Ranked for relevance and engagement.",
        "engagement": PostEngagement(reactions=10, comments=3),
    }


def test_ranked_post_rejects_fewer_than_three_comments():
    with pytest.raises(ValidationError):
        RankedPost(
            **_base_ranked_post_payload(),
            suggested_comments=[
                SuggestedComment(id="rank-1-comment-1", text="One."),
                SuggestedComment(id="rank-1-comment-2", text="Two."),
            ],
        )


def test_ranked_post_accepts_exactly_three_comments():
    ranked_post = RankedPost(
        **_base_ranked_post_payload(),
        suggested_comments=[
            SuggestedComment(id="rank-1-comment-1", text="One."),
            SuggestedComment(id="rank-1-comment-2", text="Two."),
            SuggestedComment(id="rank-1-comment-3", text="Three?"),
        ],
    )

    assert len(ranked_post.suggested_comments) == 3
