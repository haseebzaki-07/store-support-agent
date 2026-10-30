from chatbot.config import Settings
from chatbot.llm.base import LLMError, LLMMessage, LLMProvider
from chatbot.llm.fake import FakeLLM
from chatbot.llm.openai_provider import OpenAIProvider

__all__ = ["FakeLLM", "LLMError", "LLMMessage", "LLMProvider", "OpenAIProvider", "build_llm"]


def build_llm(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "fake":
        return FakeLLM()
    if settings.openai_api_key is None:
        raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
    return OpenAIProvider(
        api_key=settings.openai_api_key.get_secret_value(),
        model=settings.llm_model,
        timeout_s=settings.llm_timeout_s,
        max_tokens=settings.llm_max_tokens,
    )
