from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from app.graph.pipeline import run_pipeline_stream
from app.models import GenerationRequest

router = APIRouter()


@router.post("/generate")
async def generate(request: GenerationRequest):
    """Start the agentic generation pipeline and stream results via SSE."""
    return EventSourceResponse(
        run_pipeline_stream(request),
        media_type="text/event-stream",
    )


@router.get("/health")
async def health():
    return {"status": "ok"}
