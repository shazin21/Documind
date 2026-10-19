from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """DocuMind AI Application Settings."""

    PROJECT_NAME: str = "DocuMind AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # CORS Configuration
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Storage & Upload limits
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB
    UPLOAD_DIR: Path = Path("uploads")

    # Database connection (PostgreSQL + pgvector via psycopg 3 driver)
    DATABASE_URL: str = "postgresql+psycopg://documind:documind_secret@localhost:5432/documind_db"

    # Embedding Model Configuration
    # Default: sentence-transformers/all-MiniLM-L6-v2 produces 384-dimensional normalized vectors
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32

    # Chunking Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150

    # Reranking Configuration
    ENABLE_RERANKER: bool = False
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANK_CANDIDATE_POOL: int = 20
    RERANK_TOP_K: int = 5

    # LLM Provider Configuration
    # Supported: "mock", "gemini", "openai", "groq"
    LLM_PROVIDER: str = "mock"
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_API_BASE: str | None = None
    OPENAI_BASE_URL: str | None = None
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_API_BASE: str = "https://api.groq.com/openai/v1"

    # Evaluation
    EVALUATION_DATASET_PATH: Path = Path("evaluation/test_cases.jsonl")

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
# Ensure upload directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
