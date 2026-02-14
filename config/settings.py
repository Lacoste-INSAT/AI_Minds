from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AIMINDS_", env_file=ENV_FILE, extra="ignore"
    )

    service_name: str = "ai_minds"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # --- Ollama (local LLM) ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = Field(
        default="qwen2.5:3b-instruct",
        validation_alias=AliasChoices("AIMINDS_OLLAMA_MODEL", "OLLAMA_MODEL"),
    )
    ollama_timeout: int = 120  # local models can be slow on first load

    # --- Qdrant ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "ai_minds_memory"

    # --- Embeddings ---
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # --- OpenRouter (kept for fallback / QDesign compat) ---
    openrouter_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "AIMINDS_OPENROUTER_API_KEY", "OPENROUTER_API_KEY"
        ),
    )
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "qwen/qwen-2.5-7b-instruct:free"
    openrouter_timeout: int = 30
    openrouter_http_referer: str | None = None
    openrouter_app_title: str | None = None
    openrouter_max_retries: int = 3


settings = Settings()
