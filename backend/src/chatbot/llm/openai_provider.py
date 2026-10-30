from collections.abc import Sequence

from chatbot.llm.base import LLMMessage


class OpenAIProvider:
    """TODO(roadmap: Phase 0): real implementation.

    Needs: request timeout, bounded retries with backoff, mapping of provider errors
    (rate limit, invalid key, timeout) to `LLMError`, and `max_tokens` enforcement.
    Tests must keep using `FakeLLM`; never hit the real API from the test suite.
    """

    def __init__(self, *, api_key: str, model: str, timeout_s: float, max_tokens: int) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_s = timeout_s
        self._max_tokens = max_tokens

    async def generate(self, messages: Sequence[LLMMessage]) -> str:
        raise NotImplementedError("OpenAIProvider is not implemented yet; use LLM_PROVIDER=fake")
