"""End-to-end tests for the LinkedIn suggestion pipeline."""

import json

import pytest
from httpx import ASGITransport, AsyncClient

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


@pytest.mark.asyncio
async def test_sse_events_have_correct_format(client: AsyncClient):
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
async def test_pipeline_emits_linkedin_milestones_and_ranked_posts(
    client: AsyncClient,
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

    assert result["partial"] is False
    assert len(result["posts"]) == 3

    top_post = result["posts"][0]
    assert top_post["rank"] == 1
    assert top_post["post_url"].startswith("https://www.linkedin.com/posts/")
    assert top_post["preview"]
    assert top_post["rationale"]
    assert top_post["engagement"]["reactions"] > 0
    assert top_post["engagement"]["comments"] > 0
    assert len(top_post["suggested_comments"]) == 2
    assert all(comment["text"] for comment in top_post["suggested_comments"])
    assert "Founder" in result["request_summary"]
    assert "AI agents" in result["request_summary"]


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
