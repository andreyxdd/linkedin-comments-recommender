import json
from collections.abc import AsyncGenerator

from sse_starlette.sse import ServerSentEvent

from app.models import GenerationRequest, StreamEvent
from app.services.linkedin_discovery import ApifyLinkedInDiscoveryAdapter
from app.services.linkedin_suggestions import build_suggestion_result
from app.services.post_ranking import rank_posts


def _sse(event_type: str, stream_event: StreamEvent) -> ServerSentEvent:
    """Create a properly formatted ServerSentEvent."""
    return ServerSentEvent(
        data=stream_event.model_dump_json(),
        event=event_type,
    )


async def run_pipeline_stream(
    request: GenerationRequest,
) -> AsyncGenerator[ServerSentEvent, None]:
    """Run the LinkedIn MVP pipeline and yield SSE milestones."""
    yield _sse(
        "status",
        StreamEvent(
            event_type="status",
            node="input",
            message="Locking in your positioning",
        ),
    )

    adapter = ApifyLinkedInDiscoveryAdapter()

    yield _sse(
        "status",
        StreamEvent(
            event_type="status",
            node="discovery",
            message="Searching public LinkedIn posts",
        ),
    )
    discovered_posts = await adapter.discover(request)

    yield _sse(
        "status",
        StreamEvent(
            event_type="status",
            node="ranking",
            message="Scoring relevance and engagement",
        ),
    )
    ranked_posts = rank_posts(request, discovered_posts)

    yield _sse(
        "status",
        StreamEvent(
            event_type="status",
            node="comment_generation",
            message="Generating tailored comments",
        ),
    )
    result = build_suggestion_result(request, ranked_posts)

    result_event = StreamEvent(
        event_type="result",
        node="complete",
        message="Suggestions ready.",
        data=json.loads(result.model_dump_json()),
    )
    yield _sse("result", result_event)
