from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Agentic Loop API"
    debug: bool = False

    # LLM configuration
    llm_provider: str = "anthropic"  # "anthropic" or "openai"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Generation model (creative tasks)
    generation_model: str = "claude-sonnet-4-20250514"
    # Evaluation model (structured judgment — can be cheaper/faster)
    evaluation_model: str = "claude-haiku-4-5-20251001"

    # Graph configuration
    max_iterations: int = 3
    min_quality_score: float = 0.7

    # CORS
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
