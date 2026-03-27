from typing import TypedDict

from app.models import DataItem, DraftOutput


class GraphState(TypedDict):
    """State that flows through the LangGraph pipeline.

    Customize this for your domain — add or remove fields as needed.
    """

    # User input
    topic: str
    context: str
    output_format: str
    difficulty: str

    # Pipeline state
    fetched_data: list[DataItem]
    analysis: str
    current_drafts: list[DraftOutput]
    iteration: int
    max_iterations: int
