from pathlib import Path

from pydantic_settings import BaseSettings

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    app_name: str = "AI Agentic Loop API"
    debug: bool = False

    # LinkedIn discovery configuration
    apify_api_token: str = ""
    apify_posts_actor_id: str = "apimaestro/linkedin-posts-search-scraper-no-cookies"
    apify_reactions_actor_id: str = "harvestapi/linkedin-post-reactions"
    reaction_enrichment_count: int = 8
    max_reactions_per_post: int = 20

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

    model_config = {"env_file": str(ENV_FILE), "extra": "ignore"}


settings = Settings()
