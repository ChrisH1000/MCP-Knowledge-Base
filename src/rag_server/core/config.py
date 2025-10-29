"""Configuration management using pydantic-settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Data directories
    RAG_DATA_DIR: Path = Field(default=Path("./data"))
    RAG_INDEX_DIR: Path = Field(default=Path("./data/index"))

    # File inclusion/exclusion
    RAG_ALLOWED_FILETYPES: str = Field(
        default=".py,.php,.js,.ts,.md,.mdx,.json,.yml,.yaml,.ini,.txt"
    )
    RAG_EXCLUDE_GLOBS: str = Field(
        default="node_modules,dist,build,.git,venv,.venv,__pycache__,*.pyc,.DS_Store"
    )

    # Embedding configuration
    RAG_EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    RAG_VECTOR_STORE: Literal["faiss", "chroma"] = Field(default="faiss")
    RAG_TOP_K: int = Field(default=8, ge=1, le=100)
    RAG_CHUNK_SIZE: int = Field(default=800, ge=100, le=5000)
    RAG_CHUNK_OVERLAP: int = Field(default=120, ge=0, le=500)

    # API Security
    RAG_API_KEY: str = Field(default="dev-secret")

    # LLM Configuration
    RAG_LLM_PROVIDER: Literal["openai", "ollama", "none"] = Field(default="none")
    OPENAI_API_KEY: str = Field(default="")
    OLLAMA_ENDPOINT: str = Field(default="http://localhost:11434")
    LLM_MODEL: str = Field(default="gpt-4o-mini")

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    @property
    def allowed_filetypes(self) -> list[str]:
        """Parse allowed filetypes into a list."""
        return [ft.strip() for ft in self.RAG_ALLOWED_FILETYPES.split(",")]

    @property
    def exclude_globs(self) -> list[str]:
        """Parse exclude globs into a list."""
        return [glob.strip() for glob in self.RAG_EXCLUDE_GLOBS.split(",")]

    def model_dump_safe(self) -> dict[str, any]:
        """Dump config with secrets redacted."""
        data = self.model_dump()
        if data.get("OPENAI_API_KEY"):
            data["OPENAI_API_KEY"] = "***REDACTED***"
        if data.get("RAG_API_KEY"):
            data["RAG_API_KEY"] = "***REDACTED***"
        # Convert Path objects to strings for JSON serialization
        for key, value in data.items():
            if isinstance(value, Path):
                data[key] = str(value)
        return data


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        # Ensure directories exist
        _settings.RAG_DATA_DIR.mkdir(parents=True, exist_ok=True)
        _settings.RAG_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    return _settings
