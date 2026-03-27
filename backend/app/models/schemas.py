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


class ToneProfile(BaseModel):
    """User-controlled voice settings for suggested LinkedIn comments."""

    professional_casual: int = Field(..., ge=0, le=100)
    reserved_warm: int = Field(..., ge=0, le=100)
    measured_bold: int = Field(..., ge=0, le=100)
    conventional_fresh: int = Field(..., ge=0, le=100)


class SuggestionRequest(BaseModel):
    """Structured request contract for the LinkedIn suggestion flow."""

    persona: str = Field(..., min_length=1, description="Who the user is on LinkedIn")
    topic: str = Field(
        ..., min_length=1, description="Primary niche or conversation area"
    )
    keywords: list[str] = Field(
        ...,
        min_length=1,
        description="Include-only keywords that steer post discovery",
    )
    tone: ToneProfile


class PostEngagement(BaseModel):
    """Engagement context surfaced alongside a ranked suggestion."""

    reactions: int = Field(..., ge=0)
    comments: int = Field(..., ge=0)


class SuggestedComment(BaseModel):
    """A single copy-ready comment suggestion."""

    id: str
    text: str


class ReactionSample(BaseModel):
    """A sampled reaction record used for downstream enrichment."""

    reactor_name: str
    reactor_headline: str = ""
    reactor_profile_url: str = ""
    reaction_type: str


class NormalizedLinkedInPost(BaseModel):
    """Stable internal post record derived from external Apify payloads."""

    activity_id: str
    post_url: str
    author_name: str
    author_headline: str = ""
    author_profile_url: str = ""
    preview: str
    full_text: str
    hashtags: list[str] = Field(default_factory=list)
    total_reactions: int = Field(default=0, ge=0)
    total_comments: int = Field(default=0, ge=0)
    total_shares: int = Field(default=0, ge=0)
    reaction_types: list[str] = Field(default_factory=list)
    reaction_samples: list[ReactionSample] = Field(default_factory=list)
    published_timestamp: int = 0
    search_query: str = ""


class RankedPost(BaseModel):
    """A ranked public post suggestion for the user to engage with."""

    rank: int = Field(..., ge=1)
    author: str
    author_headline: str
    post_url: str
    preview: str
    rationale: str
    engagement: PostEngagement
    suggested_comments: list[SuggestedComment] = Field(..., min_length=2, max_length=2)


class SuggestionResult(BaseModel):
    """Final result contract returned by the mocked LinkedIn flow."""

    posts: list[RankedPost] = Field(..., min_length=1, max_length=3)
    partial: bool = False
    request_summary: str


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


# Backwards-compatible aliases while the codebase transitions away from the template.
GenerationRequest = SuggestionRequest


class StreamEvent(BaseModel):
    """SSE event sent to the frontend during processing."""

    event_type: str  # "status", "evaluation", "result"
    node: str
    message: str = ""
    data: dict = Field(default_factory=dict)
