from collections.abc import Sequence

from chatbot.llm.base import LLMMessage


class FakeLLM:
    """Deterministic provider for tests and key-free local development."""

    async def generate(self, messages: Sequence[LLMMessage]) -> str:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return f"[fake-llm] Thanks for reaching out! You said: {last_user}"
