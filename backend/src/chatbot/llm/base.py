from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: Literal["system", "user", "assistant"]
    content: str


class LLMError(Exception):
    """Raised by providers for failures the caller may want to handle (timeout, rate limit...)."""


class LLMProvider(Protocol):
    """The only way application code talks to an LLM. Tests use FakeLLM."""

    async def generate(self, messages: Sequence[LLMMessage]) -> str: ...
