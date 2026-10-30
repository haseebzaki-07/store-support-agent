from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://chatbot:chatbot@localhost:5432/chatbot"

    llm_provider: Literal["fake", "openai"] = "fake"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_s: float = 30.0
    llm_max_tokens: int = 500
    openai_api_key: SecretStr | None = None

    # How many recent messages are sent to the LLM as conversation context.
    history_window: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
