"""Vendor-neutral LLM access.

Application code only sees `LLMProvider`. This module implements it on top of LangChain chat
models, so switching between OpenAI, Anthropic, Gemini, Ollama or any OpenAI-compatible server
is a configuration change (LLM_PROVIDER / LLM_MODEL / LLM_BASE_URL), not a code change.

Provider packages are optional extras (see pyproject.toml) and imported lazily.

TODO(T1.4): extend the provider interface with tool calling.
TODO(T1.5): bounded retries/backoff and per-turn deadlines.
TODO(later): Azure OpenAI and AWS Bedrock (need provider-specific settings).
"""

from collections.abc import Callable, Sequence
from typing import Any, cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from chatbot.config import Settings
from chatbot.llm.base import LLMError, LLMMessage

InitModel = Callable[..., BaseChatModel]

# LLM_PROVIDER value -> optional-dependency extra that installs its integration package.
PROVIDER_EXTRAS = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google_genai": "google",
    "ollama": "ollama",
}


def model_kwargs(settings: Settings) -> dict[str, Any]:
    """Translate our settings into each integration's constructor arguments.

    Integrations name the same options differently (max_tokens vs num_predict, how the timeout
    is passed, api_key vs google_api_key). Optional values are omitted when unset so the
    provider SDK falls back to its own environment variables and defaults.
    """
    api_key = settings.llm_api_key.get_secret_value() if settings.llm_api_key else None
    kwargs: dict[str, Any] = {}

    match settings.llm_provider:
        case "openai" | "anthropic":
            kwargs |= {"timeout": settings.llm_timeout_s, "max_tokens": settings.llm_max_tokens}
            if api_key:
                kwargs["api_key"] = api_key
        case "google_genai":
            kwargs |= {"timeout": settings.llm_timeout_s, "max_tokens": settings.llm_max_tokens}
            if api_key:
                kwargs["google_api_key"] = api_key
        case "ollama":
            kwargs |= {
                "num_predict": settings.llm_max_tokens,
                "client_kwargs": {"timeout": settings.llm_timeout_s},
            }
        case _:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

    if settings.llm_base_url:
        kwargs["base_url"] = settings.llm_base_url
    return kwargs


def _default_init_model() -> InitModel:
    from langchain.chat_models import init_chat_model

    return cast("InitModel", init_chat_model)


def build_langchain_provider(
    settings: Settings, init_model: InitModel | None = None
) -> "LangChainProvider":
    provider = settings.llm_provider
    if not settings.llm_model:
        raise RuntimeError("LLM_MODEL is required when LLM_PROVIDER is not 'fake'")
    factory = init_model or _default_init_model()
    try:
        model = factory(settings.llm_model, model_provider=provider, **model_kwargs(settings))
    except ImportError as exc:
        extra = PROVIDER_EXTRAS[provider]
        raise RuntimeError(
            f"LLM_PROVIDER={provider} needs its integration package. "
            f"Install it with: cd backend && uv sync --extra {extra}"
        ) from exc
    return LangChainProvider(model)


class LangChainProvider:
    """`LLMProvider` backed by any LangChain chat model."""

    def __init__(self, model: BaseChatModel) -> None:
        self._model = model

    async def generate(self, messages: Sequence[LLMMessage]) -> str:
        try:
            result = await self._model.ainvoke([_to_langchain(m) for m in messages])
        except Exception as exc:  # provider SDKs raise many different exception types
            raise LLMError("LLM request failed") from exc
        return _text(result.content)


def _to_langchain(message: LLMMessage) -> BaseMessage:
    match message.role:
        case "system":
            return SystemMessage(content=message.content)
        case "assistant":
            return AIMessage(content=message.content)
        case _:
            return HumanMessage(content=message.content)


def _text(content: str | list[str | dict[str, Any]]) -> str:
    """Providers return either a string or a list of content blocks; keep only the text."""
    if isinstance(content, str):
        return content
    return "".join(
        block if isinstance(block, str) else str(block.get("text", ""))
        for block in content
        if isinstance(block, str) or block.get("type") == "text"
    )
