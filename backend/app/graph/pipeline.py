import json
from collections.abc import AsyncGenerator
from functools import partial

from langgraph.graph import END, StateGraph
from sse_starlette.sse import ServerSentEvent

from app.config import settings
from app.models import GenerationRequest, GenerationResult, StreamEvent
from app.services.data_fetcher import DataFetcher, WikipediaFetcher

from .nodes import (
    analyze_content,
    evaluate_quality,
    fetch_sources,
    generate_material,
    should_continue,
)
from .state import GraphState


def build_graph(fetcher: DataFetcher | None = None) -> StateGraph:
    """Build the LangGraph pipeline.

    Args:
        fetcher: Data fetcher implementation. Defaults to WikipediaFetcher.
    """
    if fetcher is None:
        fetcher = WikipediaFetcher()

    graph = StateGraph(GraphState)

    graph.add_node("fetch_sources", partial(fetch_sources, fetcher=fetcher))
    graph.add_node("analyze_content", analyze_content)
    graph.add_node("generate_material", generate_material)
    graph.add_node("evaluate_quality", evaluate_quality)

    graph.set_entry_point("fetch_sources")
    graph.add_edge("fetch_sources", "analyze_content")
    graph.add_edge("analyze_content", "generate_material")
    graph.add_edge("generate_material", "evaluate_quality")

    graph.add_conditional_edges(
        "evaluate_quality",
        should_continue,
        {
            "regenerate": "generate_material",
            "finish": END,
        },
    )

    return graph


def _sse(event_type: str, stream_event: StreamEvent) -> ServerSentEvent:
    """Create a properly formatted ServerSentEvent."""
    return ServerSentEvent(
        data=stream_event.model_dump_json(),
        event=event_type,
    )


async def run_pipeline_stream(
    request: GenerationRequest,
    fetcher: DataFetcher | None = None,
) -> AsyncGenerator[ServerSentEvent, None]:
    """Run the pipeline and yield SSE events."""
    graph = build_graph(fetcher)
    app = graph.compile()

    initial_state: GraphState = {
        "topic": request.topic,
        "context": request.context,
        "output_format": request.output_format.value,
        "difficulty": request.difficulty.value,
        "fetched_data": [],
        "analysis": "",
        "current_drafts": [],
        "iteration": 0,
        "max_iterations": settings.max_iterations,
    }

    node_messages = {
        "fetch_sources": "Fetching source data...",
        "analyze_content": "Analyzing content for key concepts...",
        "generate_material": "Generating draft content...",
        "evaluate_quality": "Evaluating draft quality...",
    }

    # Track state as we stream so we don't need to re-run the graph
    latest_state = dict(initial_state)

    async for event in app.astream(initial_state, stream_mode="updates"):
        for node_name, node_output in event.items():
            # Merge node output into tracked state
            latest_state.update(node_output)

            # Send status event
            status_event = StreamEvent(
                event_type="status",
                node=node_name,
                message=node_messages.get(node_name, f"Processing {node_name}..."),
            )
            yield _sse("status", status_event)

            # Send evaluation event if we just evaluated
            if node_name == "evaluate_quality" and "current_drafts" in node_output:
                drafts = node_output["current_drafts"]
                if drafts and drafts[-1].evaluation:
                    eval_data = drafts[-1].evaluation
                    eval_event = StreamEvent(
                        event_type="evaluation",
                        node=node_name,
                        message=(
                            "Draft passed quality check!"
                            if eval_data.passed
                            else (f"Draft rejected: {eval_data.reasoning}")
                        ),
                        data={
                            "accuracy_score": eval_data.accuracy_score,
                            "completeness_score": eval_data.completeness_score,
                            "clarity_score": eval_data.clarity_score,
                            "passed": eval_data.passed,
                            "reasoning": eval_data.reasoning,
                        },
                    )
                    yield _sse("evaluation", eval_event)

    # Build result from tracked state (no second graph run)
    all_drafts = latest_state.get("current_drafts", [])
    passed_drafts = [d for d in all_drafts if d.evaluation and d.evaluation.passed]
    if not passed_drafts:
        passed_drafts = all_drafts[-1:] if all_drafts else []

    result = GenerationResult(
        drafts=passed_drafts,
        iterations=latest_state.get("iteration", 0),
        sources_used=len(latest_state.get("fetched_data", [])),
    )
    result_event = StreamEvent(
        event_type="result",
        node="complete",
        message="Generation complete!",
        data=json.loads(result.model_dump_json()),
    )
    yield _sse("result", result_event)
