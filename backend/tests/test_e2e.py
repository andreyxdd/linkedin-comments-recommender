"""End-to-end tests for the LinkedIn suggestion pipeline."""

import json
from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from app.config import settings
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _parse_sse_events(raw: str) -> list[dict]:
    """Parse raw SSE text into a list of {event, data} dicts."""
    events = []
    current_event = ""
    current_data = ""

    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("event: "):
            current_event = line[7:]
        elif line.startswith("data: "):
            current_data = line[6:]
        elif line == "" and current_data:
            events.append(
                {
                    "event": current_event,
                    "data": json.loads(current_data),
                }
            )
            current_event = ""
            current_data = ""
        elif line.startswith(": "):
            # SSE comment / ping — skip
            continue

    return events


def _posts_fixture() -> list[dict]:
    return [
        {
            "activity_id": "1001",
            "post_url": "https://www.linkedin.com/posts/alpha_founder-ai-agents-distribution-1001",
            "text": (
                "AI agents are only useful when founders pair them with "
                "distribution systems that create compounding feedback loops."
            ),
            "full_urn": "urn:li:ugcPost:1001",
            "author": {
                "name": "Alpha Founder",
                "headline": "Founder building AI workflow products",
                "profile_id": "alpha-1",
                "profile_url": "https://www.linkedin.com/in/alpha-founder",
            },
            "stats": {
                "total_reactions": 45,
                "comments": 12,
                "shares": 3,
                "reactions": [{"type": "LIKE", "count": 45}],
            },
            "posted_at": {"timestamp": 1700000300},
            "hashtags": ["AIAgents", "Distribution"],
            "content": {"type": "article"},
            "is_reshare": False,
            "metadata": {"total_count": 4},
            "search_input": "AI agents linkedin distribution founder",
        },
        {
            "activity_id": "1002",
            "post_url": "https://www.linkedin.com/posts/bravo_leadership-productivity-1002",
            "text": "Leadership habits that improve general team productivity.",
            "full_urn": "urn:li:ugcPost:1002",
            "author": {
                "name": "Bravo Executive",
                "headline": "Executive coach",
                "profile_id": "bravo-1",
                "profile_url": "https://www.linkedin.com/in/bravo-executive",
            },
            "stats": {
                "total_reactions": 600,
                "comments": 180,
                "shares": 40,
                "reactions": [{"type": "LIKE", "count": 600}],
            },
            "posted_at": {"timestamp": 1700000200},
            "hashtags": ["Leadership"],
            "content": {"type": "article"},
            "is_reshare": False,
            "metadata": {"total_count": 4},
            "search_input": "AI agents linkedin distribution founder",
        },
        {
            "activity_id": "1003",
            "post_url": "https://www.linkedin.com/posts/charlie_ai-agents-gtm-1003",
            "text": (
                "Distribution loops matter more than model novelty when AI agents "
                "need to earn trust in GTM workflows."
            ),
            "full_urn": "urn:li:ugcPost:1003",
            "author": {
                "name": "Charlie Operator",
                "headline": "Operator scaling GTM systems",
                "profile_id": "charlie-1",
                "profile_url": "https://www.linkedin.com/in/charlie-operator",
            },
            "stats": {
                "total_reactions": 90,
                "comments": 21,
                "shares": 6,
                "reactions": [{"type": "INTEREST", "count": 90}],
            },
            "posted_at": {"timestamp": 1700000100},
            "hashtags": ["AIAgents", "GTM"],
            "content": {"type": "article"},
            "is_reshare": False,
            "metadata": {"total_count": 4},
            "search_input": "AI agents linkedin distribution founder",
        },
        {
            "activity_id": "1004",
            "post_url": "https://www.linkedin.com/posts/delta_ai-agents-founder-growth-1004",
            "text": (
                "Founders using AI agents for distribution should study how "
                "comment velocity shapes qualified demand."
            ),
            "full_urn": "urn:li:ugcPost:1004",
            "author": {
                "name": "Delta Founder",
                "headline": "Founder sharing weekly growth experiments",
                "profile_id": "delta-1",
                "profile_url": "https://www.linkedin.com/in/delta-founder",
            },
            "stats": {
                "total_reactions": 120,
                "comments": 35,
                "shares": 8,
                "reactions": [{"type": "PRAISE", "count": 120}],
            },
            "posted_at": {"timestamp": 1700000400},
            "hashtags": ["AIAgents", "Growth"],
            "content": {"type": "article"},
            "is_reshare": False,
            "metadata": {"total_count": 4},
            "search_input": "AI agents linkedin distribution founder",
        },
    ]


def _reactions_fixture() -> list[dict]:
    return [
        {
            "id": "reaction-1",
            "reactionType": "LIKE",
            "postId": "urn:li:ugcPost:1001",
            "actor": {
                "id": "reactor-1",
                "name": "Alice Signal",
                "linkedinUrl": "https://www.linkedin.com/in/alice-signal",
                "position": "Revenue operator",
            },
            "query": {
                "post": "https://www.linkedin.com/posts/alpha_founder-ai-agents-distribution-1001"
            },
        },
        {
            "id": "reaction-2",
            "reactionType": "INTEREST",
            "postId": "urn:li:ugcPost:1004",
            "actor": {
                "id": "reactor-2",
                "name": "Ben Demand",
                "linkedinUrl": "https://www.linkedin.com/in/ben-demand",
                "position": "Founder",
            },
            "query": {
                "post": "https://www.linkedin.com/posts/delta_ai-agents-founder-growth-1004"
            },
        },
        {
            "id": "reaction-3",
            "reactionType": "LIKE",
            "postId": "urn:li:ugcPost:1003",
            "actor": {
                "id": "reactor-3",
                "name": "Cara Pipeline",
                "linkedinUrl": "https://www.linkedin.com/in/cara-pipeline",
                "position": "Growth strategist",
            },
            "query": {
                "post": "https://www.linkedin.com/posts/charlie_ai-agents-gtm-1003"
            },
        },
    ]


def _generated_comment_payload(first: str, second: str, third: str) -> str:
    return json.dumps({"comments": [first, second, third]})


@pytest.mark.asyncio
@respx.mock
async def test_sse_events_have_correct_format(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "apify_api_token", "test-token")
    monkeypatch.setattr(settings, "reaction_enrichment_count", 4)
    monkeypatch.setattr(settings, "max_reactions_per_post", 5)

    respx.post(
        "https://api.apify.com/v2/acts/apimaestro~linkedin-posts-search-scraper-no-cookies/run-sync-get-dataset-items"
    ).mock(return_value=Response(200, json=_posts_fixture()))
    respx.post(
        "https://api.apify.com/v2/acts/harvestapi~linkedin-post-reactions/run-sync-get-dataset-items"
    ).mock(return_value=Response(200, json=_reactions_fixture()))

    response = await client.post(
        "/api/generate",
        json={
            "persona": "Founder",
            "topic": "AI agents",
            "keywords": ["linkedin", "distribution"],
            "tone": {
                "professional_casual": 62,
                "reserved_warm": 68,
                "measured_bold": 71,
                "conventional_fresh": 57,
            },
        },
    )

    assert response.status_code == 200
    raw = response.text
    assert "data: event:" not in raw
    assert "data: data:" not in raw
    assert "event: status" in raw
    assert "event: result" in raw


@pytest.mark.asyncio
@respx.mock
async def test_pipeline_emits_linkedin_milestones_and_ranked_posts(
    client: AsyncClient,
    monkeypatch,
):
    monkeypatch.setattr(settings, "apify_api_token", "test-token")
    monkeypatch.setattr(settings, "reaction_enrichment_count", 4)
    monkeypatch.setattr(settings, "max_reactions_per_post", 5)

    posts_route = respx.post(
        "https://api.apify.com/v2/acts/apimaestro~linkedin-posts-search-scraper-no-cookies/run-sync-get-dataset-items"
    ).mock(return_value=Response(200, json=_posts_fixture()))
    reactions_route = respx.post(
        "https://api.apify.com/v2/acts/harvestapi~linkedin-post-reactions/run-sync-get-dataset-items"
    ).mock(return_value=Response(200, json=_reactions_fixture()))

    generation_model = AsyncMock()
    generation_model.ainvoke = AsyncMock(
        side_effect=[
            AsyncMock(
                content=_generated_comment_payload(
                    "Comment 1A",
                    "Comment 1B",
                    "Comment 1C?",
                )
            ),
            AsyncMock(
                content=_generated_comment_payload(
                    "Comment 2A",
                    "Comment 2B",
                    "Comment 2C?",
                )
            ),
            AsyncMock(
                content=_generated_comment_payload(
                    "Comment 3A",
                    "Comment 3B",
                    "Comment 3C?",
                )
            ),
        ]
    )

    with patch(
        "app.services.linkedin_suggestions.get_generation_model",
        return_value=generation_model,
        create=True,
    ):
        response = await client.post(
            "/api/generate",
            json={
                "persona": "Founder",
                "topic": "AI agents",
                "keywords": ["linkedin", "distribution"],
                "tone": {
                    "professional_casual": 62,
                    "reserved_warm": 68,
                    "measured_bold": 71,
                    "conventional_fresh": 57,
                },
            },
        )

    events = _parse_sse_events(response.text)
    status_nodes = [e["data"]["node"] for e in events if e["event"] == "status"]
    assert status_nodes == [
        "input",
        "discovery",
        "ranking",
        "comment_generation",
    ]

    result_events = [e for e in events if e["event"] == "result"]
    assert len(result_events) == 1
    result = result_events[0]["data"]["data"]

    assert posts_route.called
    assert reactions_route.called
    assert result["partial"] is False
    assert len(result["posts"]) == 3

    ranked_authors = [post["author"] for post in result["posts"]]
    assert ranked_authors == [
        "Delta Founder",
        "Alpha Founder",
        "Charlie Operator",
    ]

    top_post = result["posts"][0]
    assert top_post["rank"] == 1
    assert top_post["post_url"] == _posts_fixture()[3]["post_url"]
    assert top_post["preview"].startswith("Founders using AI agents")
    assert top_post["full_text"].startswith("Founders using AI agents")
    assert "relevance" in top_post["rationale"].lower()
    assert top_post["engagement"]["reactions"] == 120
    assert top_post["engagement"]["comments"] == 35
    assert len(top_post["suggested_comments"]) == 3
    assert all(comment["text"] for comment in top_post["suggested_comments"])
    assert "Founder" in result["request_summary"]
    assert "AI agents" in result["request_summary"]


@pytest.mark.asyncio
@respx.mock
async def test_pipeline_returns_generated_comments_for_each_ranked_post(
    client: AsyncClient,
    monkeypatch,
):
    monkeypatch.setattr(settings, "apify_api_token", "test-token")
    monkeypatch.setattr(settings, "reaction_enrichment_count", 4)
    monkeypatch.setattr(settings, "max_reactions_per_post", 5)

    respx.post(
        "https://api.apify.com/v2/acts/apimaestro~linkedin-posts-search-scraper-no-cookies/run-sync-get-dataset-items"
    ).mock(return_value=Response(200, json=_posts_fixture()))
    respx.post(
        "https://api.apify.com/v2/acts/harvestapi~linkedin-post-reactions/run-sync-get-dataset-items"
    ).mock(return_value=Response(200, json=_reactions_fixture()))

    generation_model = AsyncMock()
    generation_model.ainvoke = AsyncMock(
        side_effect=[
            AsyncMock(
                content=_generated_comment_payload(
                    "Generated comment 1A",
                    "Generated comment 1B",
                    "Generated comment 1C?",
                )
            ),
            AsyncMock(
                content=_generated_comment_payload(
                    "Generated comment 2A",
                    "Generated comment 2B",
                    "Generated comment 2C?",
                )
            ),
            AsyncMock(
                content=_generated_comment_payload(
                    "Generated comment 3A",
                    "Generated comment 3B",
                    "Generated comment 3C?",
                )
            ),
        ]
    )

    with patch(
        "app.services.linkedin_suggestions.get_generation_model",
        return_value=generation_model,
        create=True,
    ):
        response = await client.post(
            "/api/generate",
            json={
                "persona": "Founder",
                "topic": "AI agents",
                "keywords": ["linkedin", "distribution"],
                "tone": {
                    "professional_casual": 62,
                    "reserved_warm": 68,
                    "measured_bold": 71,
                    "conventional_fresh": 57,
                },
            },
        )

    result = [
        event["data"]["data"]
        for event in _parse_sse_events(response.text)
        if event["event"] == "result"
    ][0]

    assert generation_model.ainvoke.await_count == 3
    assert result["posts"][0]["suggested_comments"][0]["text"] == "Generated comment 1A"
    assert result["posts"][0]["suggested_comments"][1]["text"] == "Generated comment 1B"
    assert result["posts"][0]["suggested_comments"][2]["text"] == "Generated comment 1C?"
    assert result["posts"][1]["suggested_comments"][0]["text"] == "Generated comment 2A"
    assert result["posts"][1]["suggested_comments"][1]["text"] == "Generated comment 2B"
    assert result["posts"][1]["suggested_comments"][2]["text"] == "Generated comment 2C?"
    assert result["posts"][2]["suggested_comments"][0]["text"] == "Generated comment 3A"
    assert result["posts"][2]["suggested_comments"][1]["text"] == "Generated comment 3B"
    assert result["posts"][2]["suggested_comments"][2]["text"] == "Generated comment 3C?"


@pytest.mark.asyncio
@respx.mock
async def test_pipeline_returns_partial_result_when_reaction_enrichment_fails(
    client: AsyncClient,
    monkeypatch,
):
    monkeypatch.setattr(settings, "apify_api_token", "test-token")
    monkeypatch.setattr(settings, "reaction_enrichment_count", 4)
    monkeypatch.setattr(settings, "max_reactions_per_post", 5)

    respx.post(
        "https://api.apify.com/v2/acts/apimaestro~linkedin-posts-search-scraper-no-cookies/run-sync-get-dataset-items"
    ).mock(return_value=Response(200, json=_posts_fixture()))
    respx.post(
        "https://api.apify.com/v2/acts/harvestapi~linkedin-post-reactions/run-sync-get-dataset-items"
    ).mock(return_value=Response(503, json={"error": "upstream unavailable"}))

    generation_model = AsyncMock()
    generation_model.ainvoke = AsyncMock(
        side_effect=[
            AsyncMock(
                content=_generated_comment_payload(
                    "Comment 1A",
                    "Comment 1B",
                    "Comment 1C?",
                )
            ),
            AsyncMock(
                content=_generated_comment_payload(
                    "Comment 2A",
                    "Comment 2B",
                    "Comment 2C?",
                )
            ),
            AsyncMock(
                content=_generated_comment_payload(
                    "Comment 3A",
                    "Comment 3B",
                    "Comment 3C?",
                )
            ),
        ]
    )

    with patch(
        "app.services.linkedin_suggestions.get_generation_model",
        return_value=generation_model,
        create=True,
    ):
        response = await client.post(
            "/api/generate",
            json={
                "persona": "Founder",
                "topic": "AI agents",
                "keywords": ["linkedin", "distribution"],
                "tone": {
                    "professional_casual": 62,
                    "reserved_warm": 68,
                    "measured_bold": 71,
                    "conventional_fresh": 57,
                },
            },
        )

    assert response.status_code == 200
    result = [
        event["data"]["data"]
        for event in _parse_sse_events(response.text)
        if event["event"] == "result"
    ][0]

    assert result["partial"] is True
    assert len(result["posts"]) == 3
    assert result["recovery_message"]
    assert "rerun" in result["recovery_message"].lower()


@pytest.mark.asyncio
@respx.mock
async def test_pipeline_returns_partial_result_when_comment_generation_degrades(
    client: AsyncClient,
    monkeypatch,
):
    monkeypatch.setattr(settings, "apify_api_token", "test-token")
    monkeypatch.setattr(settings, "reaction_enrichment_count", 4)
    monkeypatch.setattr(settings, "max_reactions_per_post", 5)

    respx.post(
        "https://api.apify.com/v2/acts/apimaestro~linkedin-posts-search-scraper-no-cookies/run-sync-get-dataset-items"
    ).mock(return_value=Response(200, json=_posts_fixture()))
    respx.post(
        "https://api.apify.com/v2/acts/harvestapi~linkedin-post-reactions/run-sync-get-dataset-items"
    ).mock(return_value=Response(200, json=_reactions_fixture()))

    generation_model = AsyncMock()
    generation_model.ainvoke = AsyncMock(
        side_effect=[
            RuntimeError("temporary generation hiccup"),
            AsyncMock(content=_generated_comment_payload("Comment 2A", "Comment 2B", "Comment 2C?")),
            AsyncMock(content=_generated_comment_payload("Comment 3A", "Comment 3B", "Comment 3C?")),
        ]
    )

    with patch(
        "app.services.linkedin_suggestions.get_generation_model",
        return_value=generation_model,
        create=True,
    ):
        response = await client.post(
            "/api/generate",
            json={
                "persona": "Founder",
                "topic": "AI agents",
                "keywords": ["linkedin", "distribution"],
                "tone": {
                    "professional_casual": 62,
                    "reserved_warm": 68,
                    "measured_bold": 71,
                    "conventional_fresh": 57,
                },
            },
        )

    result = [
        event["data"]["data"]
        for event in _parse_sse_events(response.text)
        if event["event"] == "result"
    ][0]

    assert result["partial"] is True
    assert len(result["posts"]) == 3
    assert "backup path" in result["recovery_message"].lower()


@pytest.mark.asyncio
async def test_cors_allows_frontend_origin(client: AsyncClient):
    response = await client.options(
        "/api/generate",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.asyncio
async def test_cors_allows_loopback_frontend_origin(client: AsyncClient):
    response = await client.options(
        "/api/generate",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"


@pytest.mark.asyncio
async def test_cors_allows_loopback_frontend_on_worktree_port(client: AsyncClient):
    response = await client.options(
        "/api/generate",
        headers={
            "Origin": "http://127.0.0.1:3003",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3003"
