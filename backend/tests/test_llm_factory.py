from typing import Any

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel,
    GenericFakeChatModel,
)
from langchain_core.messages import AIMessage
from pydantic import ValidationError

from chatbot.config import Settings
from chatbot.llm import FakeLLM, LLMError, LLMMessage, build_langchain_provider, build_llm
from chatbot.llm.langchain_provider import model_kwargs


def make_settings(**overrides: Any) -> Settings:
    # _env_file=None keeps a developer's local .env from leaking into tests.
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def test_fake_provider_is_default_and_needs_nothing() -> None:
    assert isinstance(build_llm(make_settings()), FakeLLM)


def test_real_provider_requires_a_model() -> None:
    with pytest.raises(ValidationError, match="LLM_MODEL"):
        make_settings(llm_provider="openai")


@pytest.mark.parametrize(
    ("provider", "expected"),
    [
        (
            "openai",
            {"timeout": 12.0, "max_tokens": 77, "api_key": "k", "base_url": "http://h"},
        ),
        (
            "anthropic",
            {"timeout": 12.0, "max_tokens": 77, "api_key": "k", "base_url": "http://h"},
        ),
        (
            "google_genai",
            {"timeout": 12.0, "max_tokens": 77, "google_api_key": "k", "base_url": "http://h"},
        ),
        (
            "ollama",
            {"num_predict": 77, "client_kwargs": {"timeout": 12.0}, "base_url": "http://h"},
        ),
    ],
)
def test_model_kwargs_per_provider(provider: str, expected: dict[str, Any]) -> None:
    settings = make_settings(
        llm_provider=provider,
        llm_model="m",
        llm_api_key="k",
        llm_base_url="http://h",
        llm_timeout_s=12,
        llm_max_tokens=77,
    )
    assert model_kwargs(settings) == expected


def test_unset_optional_values_are_omitted_so_sdk_defaults_apply() -> None:
    kwargs = model_kwargs(make_settings(llm_provider="openai", llm_model="m"))
    assert "api_key" not in kwargs
    assert "base_url" not in kwargs


async def test_provider_passes_model_and_returns_text() -> None:
    seen: dict[str, Any] = {}

    def init_model(model: str, **kwargs: Any) -> BaseChatModel:
        seen["model"] = model
        seen.update(kwargs)
        return FakeListChatModel(responses=["hi there"])

    provider = build_langchain_provider(
        make_settings(llm_provider="anthropic", llm_model="some-model"), init_model
    )
    reply = await provider.generate([LLMMessage("system", "s"), LLMMessage("user", "u")])

    assert reply == "hi there"
    assert seen["model"] == "some-model"
    assert seen["model_provider"] == "anthropic"


async def test_content_blocks_are_joined_into_text() -> None:
    model = GenericFakeChatModel(
        messages=iter(
            [
                AIMessage(
                    content=[
                        {"type": "text", "text": "Hello, "},
                        {"type": "tool_use", "id": "x", "name": "n", "input": {}},
                        {"type": "text", "text": "world"},
                    ]
                )
            ]
        )
    )
    provider = build_langchain_provider(
        make_settings(llm_provider="anthropic", llm_model="m"), lambda *_a, **_k: model
    )

    assert await provider.generate([LLMMessage("user", "hi")]) == "Hello, world"


def test_missing_integration_package_gives_actionable_error() -> None:
    def init_model(*_args: Any, **_kwargs: Any) -> BaseChatModel:
        raise ImportError("No module named 'langchain_anthropic'")

    with pytest.raises(RuntimeError, match=r"uv sync --extra anthropic"):
        build_langchain_provider(make_settings(llm_provider="anthropic", llm_model="m"), init_model)


async def test_provider_failures_become_llm_error() -> None:
    class Boom(BaseChatModel):
        @property
        def _llm_type(self) -> str:
            return "boom"

        def _generate(self, *_args: Any, **_kwargs: Any) -> Any:
            raise RuntimeError("provider exploded")

    provider = build_langchain_provider(
        make_settings(llm_provider="openai", llm_model="m"), lambda *_a, **_k: Boom()
    )

    with pytest.raises(LLMError):
        await provider.generate([LLMMessage("user", "hi")])
