from functools import lru_cache
from typing import Literal, Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# "fake" needs nothing and is the default. The others map to LangChain integrations; see
# chatbot/llm/langchain_provider.py. "openai" also works with any OpenAI-compatible server
# (vLLM, LM Studio, OpenRouter, ...) by setting LLM_BASE_URL.
LLMProviderName = Literal["fake", "openai", "anthropic", "google_genai", "ollama"]


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://chatbot:chatbot@localhost:5432/chatbot"

    llm_provider: LLMProviderName = "fake"
    # No vendor default on purpose: required for every provider except "fake".
    llm_model: str | None = None
    # Optional. When unset, the provider's usual env var is used (OPENAI_API_KEY,
    # ANTHROPIC_API_KEY, GOOGLE_API_KEY). Not needed for Ollama.
    llm_api_key: SecretStr | None = None
    # Optional endpoint override (OpenAI-compatible servers, Ollama on another host, proxies).
    llm_base_url: str | None = None
    llm_timeout_s: float = 30.0
    llm_max_tokens: int = 500

    # How many recent messages are sent to the LLM as conversation context.
    history_window: int = 10

    @model_validator(mode="after")
    def _model_required_for_real_providers(self) -> Self:
        if self.llm_provider != "fake" and not self.llm_model:
            raise ValueError("LLM_MODEL is required when LLM_PROVIDER is not 'fake'")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
