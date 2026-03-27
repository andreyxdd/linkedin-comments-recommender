from langchain_core.language_models import BaseChatModel

from app.config import settings


def get_generation_model() -> BaseChatModel:
    """Get the LLM for creative/generation tasks."""
    return _get_model(settings.generation_model)


def get_evaluation_model() -> BaseChatModel:
    """Get the LLM for evaluation/judgment tasks (can be cheaper)."""
    return _get_model(settings.evaluation_model)


def _get_model(model_name: str) -> BaseChatModel:
    provider = settings.llm_provider

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model_name,
            api_key=settings.anthropic_api_key,
            max_tokens=4096,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            api_key=settings.openai_api_key,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
