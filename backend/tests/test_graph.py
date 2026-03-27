from app.graph.nodes import _parse_evaluation, should_continue
from app.graph.state import GraphState
from app.models import DraftEvaluation, DraftOutput


def _make_state(**overrides) -> GraphState:
    defaults: GraphState = {
        "topic": "test",
        "context": "general",
        "output_format": "summary",
        "difficulty": "intermediate",
        "fetched_data": [],
        "analysis": "",
        "current_drafts": [],
        "iteration": 0,
        "max_iterations": 3,
    }
    defaults.update(overrides)
    return defaults


def test_should_continue_finishes_when_passed():
    draft = DraftOutput(
        content="test",
        evaluation=DraftEvaluation(
            accuracy_score=0.9,
            completeness_score=0.9,
            clarity_score=0.9,
            passed=True,
            reasoning="Good",
        ),
    )
    state = _make_state(current_drafts=[draft], iteration=1)
    assert should_continue(state) == "finish"


def test_should_continue_finishes_at_max_iterations():
    draft = DraftOutput(
        content="test",
        evaluation=DraftEvaluation(
            accuracy_score=0.5,
            completeness_score=0.5,
            clarity_score=0.5,
            passed=False,
            reasoning="Needs work",
        ),
    )
    state = _make_state(current_drafts=[draft], iteration=3, max_iterations=3)
    assert should_continue(state) == "finish"


def test_should_continue_regenerates_when_failed():
    draft = DraftOutput(
        content="test",
        evaluation=DraftEvaluation(
            accuracy_score=0.5,
            completeness_score=0.5,
            clarity_score=0.5,
            passed=False,
            reasoning="Needs work",
        ),
    )
    state = _make_state(current_drafts=[draft], iteration=1)
    assert should_continue(state) == "regenerate"


def test_parse_evaluation_valid():
    text = """ACCURACY: 0.85
COMPLETENESS: 0.7
CLARITY: 0.9
PASSED: true
REASONING: Content is well-structured"""
    result = _parse_evaluation(text)
    assert result.accuracy_score == 0.85
    assert result.completeness_score == 0.7
    assert result.clarity_score == 0.9
    assert result.passed is True
    assert "well-structured" in result.reasoning


def test_parse_evaluation_handles_malformed():
    text = "Some random LLM output that doesn't follow format"
    result = _parse_evaluation(text)
    assert result.accuracy_score == 0.5  # defaults
    assert result.passed is False
