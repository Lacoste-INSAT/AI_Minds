"""
Synapsis Backend — Configuration
All settings via environment variables with sensible defaults.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    # --- App ---
    app_name: str = "Synapsis"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000

    # --- Ollama ---
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model_t1: str = "phi4-mini"
    ollama_model_t2: str = "qwen2.5:3b"
    ollama_model_t3: str = "qwen2.5:0.5b"
    ollama_timeout: int = 120  # seconds

    # --- Qdrant ---
    qdrant_host: str = "127.0.0.1"
    qdrant_port: int = 6333
    qdrant_collection: str = "synapsis_chunks"
    embedding_dim: int = 384

    # --- Embeddings ---
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- SQLite ---
    sqlite_path: str = "data/synapsis.db"

    # --- Ingestion ---
    watched_directories: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(
        default_factory=lambda: ["node_modules/**", ".git/**", "*.exe", "*.dll"]
    )
    max_file_size_mb: int = 50
    scan_interval_seconds: int = 30
    rate_limit_files_per_minute: int = 10

    # --- Chunking ---
    chunk_size: int = 500
    chunk_overlap: int = 100

    # --- Retrieval ---
    retrieval_top_k: int = 10
    dense_weight: float = 0.4
    sparse_weight: float = 0.3
    graph_weight: float = 0.3

    # --- User config file ---
    user_config_path: str = "config/synapsis_config.json"

    # --- CORS ---
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    model_config = {
        "env_prefix": "SYNAPSIS_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()


def get_data_dir() -> Path:
    """Get or create the data directory."""
    data_dir = Path(settings.sqlite_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
