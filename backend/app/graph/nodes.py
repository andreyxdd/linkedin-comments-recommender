from langchain_core.messages import HumanMessage, SystemMessage

from app.models import DataItem, DraftEvaluation, DraftOutput
from app.services.data_fetcher import DataFetcher
from app.services.llm import get_evaluation_model, get_generation_model

from .state import GraphState


async def fetch_sources(state: GraphState, fetcher: DataFetcher) -> dict:
    """Fetch data from external source. Swap the fetcher for your domain."""
    items: list[DataItem] = await fetcher.fetch(state["topic"], state["context"])
    return {"fetched_data": items}


async def analyze_content(state: GraphState) -> dict:
    """Analyze fetched data to extract patterns and key insights."""
    llm = get_generation_model()
    data_text = "\n\n".join(
        f"### {item.title}\n{item.content}" for item in state["fetched_data"]
    )

    messages = [
        SystemMessage(
            content=(
                "You are an expert analyst. Analyze the following source material "
                "and extract key concepts, patterns, and important information. "
                f"Target audience level: {state['difficulty']}. "
                f"Domain context: {state['context']}."
            )
        ),
        HumanMessage(
            content=f"Analyze this material about '{state['topic']}':\n\n{data_text}"
        ),
    ]

    response = await llm.ainvoke(messages)
    return {"analysis": response.content}


async def generate_material(state: GraphState) -> dict:
    """Generate draft output based on analysis. Customize the prompt for your domain."""
    llm = get_generation_model()
    format_instructions = {
        "summary": (
            "Create a comprehensive summary with clear sections and key takeaways."
        ),
        "flashcards": (
            "Create flashcards in Q: / A: format. "
            "Each flashcard should test one specific concept."
        ),
        "quiz": (
            "Create a quiz with multiple-choice questions. "
            "Include the correct answer and brief explanation for each."
        ),
    }

    instruction = format_instructions.get(
        state["output_format"],
        "Create well-structured educational content.",
    )

    iteration_note = ""
    if state["iteration"] > 0 and state["current_drafts"]:
        last_eval = state["current_drafts"][-1].evaluation
        if last_eval:
            iteration_note = (
                f"\n\nPrevious attempt was rejected: {last_eval.reasoning}\n"
                "Improve on these specific issues."
            )

    messages = [
        SystemMessage(
            content=(
                f"You are an expert content creator. {instruction} "
                f"Difficulty level: {state['difficulty']}. "
                f"Topic: {state['topic']}. Context: {state['context']}.{iteration_note}"
            )
        ),
        HumanMessage(
            content=(
                f"Based on this analysis, generate the content:\n\n{state['analysis']}"
            )
        ),
    ]

    response = await llm.ainvoke(messages)
    new_draft = DraftOutput(content=response.content)
    return {
        "current_drafts": state["current_drafts"] + [new_draft],
        "iteration": state["iteration"] + 1,
    }


async def evaluate_quality(state: GraphState) -> dict:
    """Evaluate the latest draft against quality criteria."""
    llm = get_evaluation_model()
    latest_draft = state["current_drafts"][-1]

    messages = [
        SystemMessage(
            content=(
                "You are a strict quality evaluator. Evaluate the following content "
                "against these criteria:\n"
                "1. Accuracy: Is the content factually correct "
                "based on the source material?\n"
                "2. Completeness: Does it cover the key "
                "concepts adequately?\n"
                "3. Clarity: Is it well-structured and easy "
                "to understand at the target level?\n\n"
                "Respond in EXACTLY this format (no other text):\n"
                "ACCURACY: <score 0.0-1.0>\n"
                "COMPLETENESS: <score 0.0-1.0>\n"
                "CLARITY: <score 0.0-1.0>\n"
                "PASSED: <true or false>\n"
                "REASONING: <one sentence explanation>"
            )
        ),
        HumanMessage(
            content=(
                f"Source analysis:\n{state['analysis']}\n\n"
                f"Draft to evaluate (format: {state['output_format']}, "
                f"difficulty: {state['difficulty']}):\n\n{latest_draft.content}"
            )
        ),
    ]

    response = await llm.ainvoke(messages)
    evaluation = _parse_evaluation(response.content)

    updated_draft = DraftOutput(
        content=latest_draft.content,
        evaluation=evaluation,
    )
    updated_drafts = state["current_drafts"][:-1] + [updated_draft]
    return {"current_drafts": updated_drafts}


def should_continue(state: GraphState) -> str:
    """Conditional edge: decide whether to loop or finish."""
    latest_draft = state["current_drafts"][-1]

    if latest_draft.evaluation and latest_draft.evaluation.passed:
        return "finish"

    if state["iteration"] >= state["max_iterations"]:
        return "finish"

    return "regenerate"


def _parse_evaluation(text: str) -> DraftEvaluation:
    """Parse the structured evaluation response from the LLM."""
    lines = text.strip().split("\n")
    scores = {}
    reasoning = ""
    passed = False

    for line in lines:
        line = line.strip()
        if line.startswith("ACCURACY:"):
            scores["accuracy"] = _extract_float(line)
        elif line.startswith("COMPLETENESS:"):
            scores["completeness"] = _extract_float(line)
        elif line.startswith("CLARITY:"):
            scores["clarity"] = _extract_float(line)
        elif line.startswith("PASSED:"):
            passed = "true" in line.lower()
        elif line.startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()

    return DraftEvaluation(
        accuracy_score=scores.get("accuracy", 0.5),
        completeness_score=scores.get("completeness", 0.5),
        clarity_score=scores.get("clarity", 0.5),
        passed=passed,
        reasoning=reasoning or "No reasoning provided",
    )


def _extract_float(line: str) -> float:
    try:
        return float(line.split(":")[1].strip())
    except (ValueError, IndexError):
        return 0.5
