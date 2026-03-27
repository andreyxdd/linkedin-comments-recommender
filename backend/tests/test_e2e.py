"""End-to-end tests for the generation pipeline.

Tests the full flow: HTTP request → SSE streaming → correct event format,
with mocked LLM responses and both real and mock data fetchers.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import ASGITransport, AsyncClient, Response

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _mock_llm_response(content: str):
    """Create a mock LLM that returns a fixed response."""
    mock = AsyncMock()
    mock.ainvoke = AsyncMock(return_value=AsyncMock(content=content))
    return mock


def _passing_evaluation_response() -> str:
    return (
        "ACCURACY: 0.9\n"
        "COMPLETENESS: 0.85\n"
        "CLARITY: 0.95\n"
        "PASSED: true\n"
        "REASONING: Content meets all quality criteria"
    )


def _failing_evaluation_response() -> str:
    return (
        "ACCURACY: 0.4\n"
        "COMPLETENESS: 0.3\n"
        "CLARITY: 0.5\n"
        "PASSED: false\n"
        "REASONING: Content is too superficial"
    )


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


# -------------------------------------------------------------------
# SSE format tests (regression for double data: wrapping bug)
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sse_events_have_correct_format(client: AsyncClient):
    """SSE events must have separate event: and data: lines,
    not be wrapped inside data: prefixes."""
    gen_llm = _mock_llm_response("Analyzed content")
    eval_llm = _mock_llm_response(_passing_evaluation_response())

    with (
        patch("app.graph.nodes.get_generation_model", return_value=gen_llm),
        patch("app.graph.nodes.get_evaluation_model", return_value=eval_llm),
    ):
        response = await client.post(
            "/api/generate",
            json={"topic": "test"},
        )

    assert response.status_code == 200
    raw = response.text

    # Must NOT contain double data: wrapping
    assert "data: event:" not in raw
    assert "data: data:" not in raw

    # Must contain properly formatted event lines
    assert "event: status" in raw
    assert "event: result" in raw


@pytest.mark.asyncio
async def test_sse_events_are_valid_json(client: AsyncClient):
    """Every data: line must contain valid JSON."""
    gen_llm = _mock_llm_response("Some generated content")
    eval_llm = _mock_llm_response(_passing_evaluation_response())

    with (
        patch("app.graph.nodes.get_generation_model", return_value=gen_llm),
        patch("app.graph.nodes.get_evaluation_model", return_value=eval_llm),
    ):
        response = await client.post(
            "/api/generate",
            json={"topic": "test"},
        )

    events = _parse_sse_events(response.text)
    assert len(events) > 0

    for event in events:
        assert "event_type" in event["data"]
        assert "node" in event["data"]


# -------------------------------------------------------------------
# Full pipeline flow tests
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_produces_correct_event_sequence(
    client: AsyncClient,
):
    """Pipeline must emit status events in order:
    fetch → analyze → generate → evaluate, then result."""
    gen_llm = _mock_llm_response("Generated study guide")
    eval_llm = _mock_llm_response(_passing_evaluation_response())

    with (
        patch("app.graph.nodes.get_generation_model", return_value=gen_llm),
        patch("app.graph.nodes.get_evaluation_model", return_value=eval_llm),
    ):
        response = await client.post(
            "/api/generate",
            json={
                "topic": "gravity",
                "context": "physics",
                "output_format": "flashcards",
                "difficulty": "beginner",
            },
        )

    events = _parse_sse_events(response.text)
    status_nodes = [e["data"]["node"] for e in events if e["event"] == "status"]
    event_types = [e["event"] for e in events]

    # Status events in correct order
    assert status_nodes == [
        "fetch_sources",
        "analyze_content",
        "generate_material",
        "evaluate_quality",
    ]

    # Evaluation event present
    assert "evaluation" in event_types

    # Result is the last event
    assert event_types[-1] == "result"


@pytest.mark.asyncio
async def test_pipeline_result_contains_draft_and_metadata(
    client: AsyncClient,
):
    """The result event must contain drafts, iterations, and sources_used."""
    gen_llm = _mock_llm_response("A complete study guide")
    eval_llm = _mock_llm_response(_passing_evaluation_response())

    with (
        patch("app.graph.nodes.get_generation_model", return_value=gen_llm),
        patch("app.graph.nodes.get_evaluation_model", return_value=eval_llm),
    ):
        response = await client.post(
            "/api/generate",
            json={"topic": "biology"},
        )

    events = _parse_sse_events(response.text)
    result_events = [e for e in events if e["event"] == "result"]
    assert len(result_events) == 1

    result_data = result_events[0]["data"]["data"]
    assert "drafts" in result_data
    assert len(result_data["drafts"]) > 0
    assert result_data["iterations"] >= 1
    assert result_data["sources_used"] >= 1

    # Draft should have content and evaluation
    draft = result_data["drafts"][0]
    assert draft["content"] == "A complete study guide"
    assert draft["evaluation"]["passed"] is True


@pytest.mark.asyncio
async def test_pipeline_retries_on_failed_evaluation(
    client: AsyncClient,
):
    """When evaluation fails, pipeline should loop back and regenerate."""
    gen_llm = _mock_llm_response("Generated content")

    # First call fails, second call passes
    eval_llm = AsyncMock()
    eval_llm.ainvoke = AsyncMock(
        side_effect=[
            AsyncMock(content=_failing_evaluation_response()),
            AsyncMock(content=_passing_evaluation_response()),
        ]
    )

    with (
        patch("app.graph.nodes.get_generation_model", return_value=gen_llm),
        patch("app.graph.nodes.get_evaluation_model", return_value=eval_llm),
    ):
        response = await client.post(
            "/api/generate",
            json={"topic": "test"},
        )

    events = _parse_sse_events(response.text)
    status_nodes = [e["data"]["node"] for e in events if e["event"] == "status"]

    # Should see generate_material twice (initial + retry)
    assert status_nodes.count("generate_material") == 2
    assert status_nodes.count("evaluate_quality") == 2

    # Should have two evaluation events
    eval_events = [e for e in events if e["event"] == "evaluation"]
    assert len(eval_events) == 2
    assert eval_events[0]["data"]["data"]["passed"] is False
    assert eval_events[1]["data"]["data"]["passed"] is True

    # Result should have 2 iterations
    result = [e for e in events if e["event"] == "result"][0]
    assert result["data"]["data"]["iterations"] == 2


# -------------------------------------------------------------------
# Wikipedia User-Agent tests (regression for 403 bug)
# -------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_wikipedia_fetcher_sends_user_agent():
    """WikipediaFetcher must send a User-Agent header to avoid 403."""
    from app.services.data_fetcher import WikipediaFetcher

    search_route = respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(
            200,
            json={"query": {"search": [{"title": "Test Article"}]}},
        )
    )

    summary_route = respx.get(
        "https://en.wikipedia.org/api/rest_v1/page/summary/Test_Article"
    ).mock(
        return_value=Response(
            200,
            json={
                "title": "Test Article",
                "extract": "Test content",
                "content_urls": {
                    "desktop": {"page": "https://en.wikipedia.org/wiki/Test"}
                },
            },
        )
    )

    fetcher = WikipediaFetcher()
    items = await fetcher.fetch("test", "general")

    # Verify User-Agent was sent on both requests
    assert search_route.called
    search_request = search_route.calls[0].request
    assert "User-Agent" in search_request.headers
    assert "ai-fullstack-app" in search_request.headers["User-Agent"]

    assert summary_route.called
    summary_request = summary_route.calls[0].request
    assert "User-Agent" in summary_request.headers

    # Verify data was parsed correctly
    assert len(items) == 1
    assert items[0].title == "Test Article"
    assert items[0].content == "Test content"


@pytest.mark.asyncio
@respx.mock
async def test_wikipedia_fetcher_parses_multiple_results():
    """WikipediaFetcher should handle multiple search results."""
    from app.services.data_fetcher import WikipediaFetcher

    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(
            200,
            json={
                "query": {
                    "search": [
                        {"title": "Article One"},
                        {"title": "Article Two"},
                    ]
                }
            },
        )
    )

    for title in ["Article_One", "Article_Two"]:
        respx.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}").mock(
            return_value=Response(
                200,
                json={
                    "title": title.replace("_", " "),
                    "extract": f"Content for {title}",
                    "content_urls": {
                        "desktop": {"page": f"https://example.com/{title}"}
                    },
                },
            )
        )

    fetcher = WikipediaFetcher()
    items = await fetcher.fetch("test", "general")

    assert len(items) == 2
    assert items[0].title == "Article One"
    assert items[1].title == "Article Two"


# -------------------------------------------------------------------
# CORS tests
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cors_allows_frontend_origin(client: AsyncClient):
    """CORS preflight must allow the configured frontend origin."""
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
