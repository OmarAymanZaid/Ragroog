from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # ---------------- CONFIGURATION MECHANICS ----------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


    # ---------------- CORE SERVICE APP STATE ----------------
    APP_NAME: str = "Ragroog"
    APP_VERSION: str = "0.1"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    
    FILE_ALLOWED_TYPES: list[str] = ["text/plain", "application/pdf"]
    FILE_MAX_SIZE: int = 10  # In MB
    FILE_DEFAULT_CHUNK_SIZE: int = 512000  # 512KB

    MONGODB_URL: str
    MONGODB_DATABASE: str

    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    OPENAI_API_KEY: str = None
    OPENAI_API_URL: str = None
    COHERE_API_KEY: str = None


    GENERATION_MODEL_ID_LITERAL: list[str] = None
    GENERATION_MODEL_ID: str = None
    EMBEDDING_MODEL_ID: str = None
    EMBEDDING_MODEL_SIZE: int = None
    INPUT_DEFAULT_MAX_CHARACTERS: int = None
    GENERATION_DEFAULT_MAX_TOKENS: int = None
    GENERATION_DEFAULT_TEMPERATURE: float = None


    # ---------------- REUSABLE HELPERS ----------------
    @property
    def is_local(self) -> bool:
        """Quick boolean flag to evaluate local runtime contexts."""
        return self.ENVIRONMENT == "local"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns a cached singleton instance of the system configuration.
    
    Prevents repeated disk read operational overhead during API requests.
    """
    return Settings()