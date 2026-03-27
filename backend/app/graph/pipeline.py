import json
from collections.abc import AsyncGenerator

from sse_starlette.sse import ServerSentEvent

from app.models import GenerationRequest, StreamEvent
from app.services.linkedin_suggestions import build_mock_suggestion_result


def _sse(event_type: str, stream_event: StreamEvent) -> ServerSentEvent:
    """Create a properly formatted ServerSentEvent."""
    return ServerSentEvent(
        data=stream_event.model_dump_json(),
        event=event_type,
    )


async def run_pipeline_stream(
    request: GenerationRequest,
) -> AsyncGenerator[ServerSentEvent, None]:
    """Run the mocked LinkedIn MVP pipeline and yield SSE milestones."""
    for node_name, message in [
        ("input", "Locking in your positioning"),
        ("discovery", "Searching public LinkedIn posts"),
        ("ranking", "Scoring relevance and engagement"),
        ("comment_generation", "Generating tailored comments"),
    ]:
        yield _sse(
            "status",
            StreamEvent(
                event_type="status",
                node=node_name,
                message=message,
            ),
        )

    result = build_mock_suggestion_result(request)
    result_event = StreamEvent(
        event_type="result",
        node="complete",
        message="Suggestions ready.",
        data=json.loads(result.model_dump_json()),
    )
    yield _sse("result", result_event)
