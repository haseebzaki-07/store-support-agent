from chatbot.config import Settings
from chatbot.llm.base import LLMError, LLMMessage, LLMProvider
from chatbot.llm.fake import FakeLLM
from chatbot.llm.langchain_provider import LangChainProvider, build_langchain_provider

__all__ = [
    "FakeLLM",
    "LLMError",
    "LLMMessage",
    "LLMProvider",
    "LangChainProvider",
    "build_langchain_provider",
    "build_llm",
]


def build_llm(settings: Settings) -> LLMProvider:
    """Build the configured provider. "fake" needs no key; everything else is configuration."""
    if settings.llm_provider == "fake":
        return FakeLLM()
    return build_langchain_provider(settings)
