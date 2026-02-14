from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# AI MINDS — Personal Cognitive Assistant
# NO proprietary APIs. Local models only.


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

    # --- Ingestion ---
    watch_dir: str | None = None  # optional: auto-ingest from this folder


settings = Settings()
