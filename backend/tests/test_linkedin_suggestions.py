from unittest.mock import AsyncMock, patch

import pytest

from app.models import NormalizedLinkedInPost, SuggestionRequest, ToneProfile
from app.services.linkedin_suggestions import build_suggestion_result


def _request() -> SuggestionRequest:
    return SuggestionRequest(
        persona="Founder",
        topic="AI agents",
        keywords=["linkedin", "distribution"],
        tone=ToneProfile(
            professional_casual=62,
            reserved_warm=68,
            measured_bold=71,
            conventional_fresh=57,
        ),
    )


def _posts() -> list[NormalizedLinkedInPost]:
    first_preview = (
        "AI agents only matter when distribution loops get stronger over time."
    )
    second_preview = "Founders should measure comment velocity, not just impressions."
    third_preview = (
        "Distribution compounds when AI agents are tied to actual workflows."
    )

    return [
        NormalizedLinkedInPost(
            activity_id="1001",
            post_url="https://www.linkedin.com/posts/post-1001",
            author_name="Alpha Founder",
            author_headline="Founder building AI workflow products",
            preview=first_preview,
            full_text=first_preview,
            hashtags=["AIAgents", "Distribution"],
            total_reactions=45,
            total_comments=12,
            total_shares=3,
        ),
        NormalizedLinkedInPost(
            activity_id="1002",
            post_url="https://www.linkedin.com/posts/post-1002",
            author_name="Bravo Operator",
            author_headline="Operator scaling demand systems",
            preview=second_preview,
            full_text=second_preview,
            hashtags=["Growth"],
            total_reactions=90,
            total_comments=18,
            total_shares=4,
        ),
        NormalizedLinkedInPost(
            activity_id="1003",
            post_url="https://www.linkedin.com/posts/post-1003",
            author_name="Charlie Builder",
            author_headline="Building GTM tooling",
            preview=third_preview,
            full_text=third_preview,
            hashtags=["GTM"],
            total_reactions=120,
            total_comments=22,
            total_shares=5,
        ),
    ]


@pytest.mark.asyncio
async def test_build_suggestion_result_shapes_generated_comments():
    generation_model = AsyncMock()
    generation_model.ainvoke = AsyncMock(
        side_effect=[
            AsyncMock(
                content=(
                    "```json\n"
                    '{"comments":["  First generated comment.  ",'
                    '"Second generated comment.","Third generated question?"]}\n```'
                )
            ),
            AsyncMock(
                content=(
                    '{"comments":["Third generated comment.",'
                    '"Fourth generated comment.","Fifth generated question?"]}'
                )
            ),
            AsyncMock(
                content=(
                    '{"comments":["Fifth generated comment.",'
                    '"Sixth generated comment.","Seventh generated question?"]}'
                )
            ),
        ]
    )

    with patch(
        "app.services.linkedin_suggestions.get_generation_model",
        return_value=generation_model,
    ):
        result = await build_suggestion_result(_request(), _posts())

    assert [len(post.suggested_comments) for post in result.posts] == [3, 3, 3]
    assert result.posts[0].suggested_comments[0].id == "rank-1-comment-1"
    assert result.posts[0].suggested_comments[0].text == "First generated comment."
    assert result.posts[2].suggested_comments[1].text == "Sixth generated comment."
    assert result.posts[2].suggested_comments[2].text == "Seventh generated question?"
    assert result.posts[0].full_text == _posts()[0].full_text


@pytest.mark.asyncio
async def test_build_suggestion_result_accepts_list_payload_from_generation_model():
    generation_model = AsyncMock()
    generation_model.ainvoke = AsyncMock(
        return_value=AsyncMock(
            content=(
                '[{"text":"List payload comment 1."},'
                '{"text":"List payload comment 2."},'
                '{"text":"List payload question 3?"}]'
            )
        )
    )

    with patch(
        "app.services.linkedin_suggestions.get_generation_model",
        return_value=generation_model,
    ):
        result = await build_suggestion_result(_request(), _posts())

    assert result.posts[0].suggested_comments[0].text == "List payload comment 1."
    assert result.posts[0].suggested_comments[1].text == "List payload comment 2."
    assert result.posts[0].suggested_comments[2].text == "List payload question 3?"


@pytest.mark.asyncio
async def test_build_suggestion_result_fallback_returns_question_as_third_option():
    with patch(
        "app.services.linkedin_suggestions.get_generation_model",
        side_effect=RuntimeError("missing llm config"),
    ):
        result = await build_suggestion_result(_request(), _posts())

    for post in result.posts:
        assert len(post.suggested_comments) == 3
        assert post.suggested_comments[2].text.endswith("?")


@pytest.mark.asyncio
async def test_build_suggestion_result_marks_partial_for_discovery_warning():
    generation_model = AsyncMock()
    generation_model.ainvoke = AsyncMock(
        side_effect=[
            AsyncMock(content='{"comments":["Comment 1A.","Comment 1B.","Comment 1C?"]}'),
            AsyncMock(content='{"comments":["Comment 2A.","Comment 2B.","Comment 2C?"]}'),
            AsyncMock(content='{"comments":["Comment 3A.","Comment 3B.","Comment 3C?"]}'),
        ]
    )

    with patch(
        "app.services.linkedin_suggestions.get_generation_model",
        return_value=generation_model,
    ):
        result = await build_suggestion_result(
            _request(),
            _posts(),
            discovery_warning=(
                "Some engagement signals were unavailable. "
                "You can still use these ranked posts and rerun for a fuller result."
            ),
        )

    assert result.partial is True
    assert result.recovery_message
    assert "rerun" in result.recovery_message.lower()
