from enum import StrEnum

from pydantic import BaseModel, Field


class OutputFormat(StrEnum):
    """Output format for generated content. Customize for your domain."""

    SUMMARY = "summary"
    FLASHCARDS = "flashcards"
    QUIZ = "quiz"


class DifficultyLevel(StrEnum):
    """Difficulty/complexity level. Customize for your domain."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class GenerationRequest(BaseModel):
    """User input to the agentic loop. Customize fields for your domain."""

    topic: str = Field(..., description="The subject or keywords to process")
    context: str = Field(
        default="general",
        description="Domain or field context (e.g., 'data science', 'history')",
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.SUMMARY,
        description="Desired output format",
    )
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.INTERMEDIATE,
        description="Target difficulty level",
    )


class DataItem(BaseModel):
    """A single item fetched from the external data source."""

    title: str
    content: str
    source_url: str = ""
    metadata: dict = Field(default_factory=dict)


class DraftEvaluation(BaseModel):
    """Quality evaluation of a generated draft."""

    accuracy_score: float = Field(..., ge=0, le=1)
    completeness_score: float = Field(..., ge=0, le=1)
    clarity_score: float = Field(..., ge=0, le=1)
    passed: bool
    reasoning: str


class DraftOutput(BaseModel):
    """A single generated draft with optional evaluation."""

    content: str
    evaluation: DraftEvaluation | None = None


class GenerationResult(BaseModel):
    """Final result returned to the user."""

    drafts: list[DraftOutput]
    iterations: int
    sources_used: int


class StreamEvent(BaseModel):
    """SSE event sent to the frontend during processing."""

    event_type: str  # "status", "evaluation", "result"
    node: str
    message: str = ""
    data: dict = Field(default_factory=dict)
