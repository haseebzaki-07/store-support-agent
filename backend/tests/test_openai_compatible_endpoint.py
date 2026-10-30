"""Exercises the real OpenAI integration against a local stub server (no network, no API key).

This proves the "any OpenAI-compatible server" path: any vendor or local server that speaks
the chat-completions protocol works by setting LLM_PROVIDER=openai and LLM_BASE_URL.
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from chatbot.config import Settings
from chatbot.llm import LLMError, LLMMessage, build_llm

pytest.importorskip("langchain_openai")


@pytest.fixture
async def stub_endpoint(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[tuple[str, list[Any]]]:
    # Keep local requests off any proxy configured in the environment.
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")

    received: list[dict[str, Any]] = []
    app = FastAPI()

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request) -> JSONResponse:
        if request.headers.get("authorization") == "Bearer bad-key":
            return JSONResponse(
                {"error": {"message": "Incorrect API key", "type": "invalid_request_error"}},
                status_code=401,
            )
        received.append(await request.json())
        return JSONResponse(
            {
                "id": "chatcmpl-stub",
                "object": "chat.completion",
                "created": 0,
                "model": "stub-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "hello from stub"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }
        )

    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning"))
    task = asyncio.create_task(server.serve())
    for _ in range(500):
        if server.started:
            break
        await asyncio.sleep(0.01)
    assert server.started, "stub server did not start"
    port = server.servers[0].sockets[0].getsockname()[1]
    try:
        yield f"http://127.0.0.1:{port}/v1", received
    finally:
        server.should_exit = True
        await task


def _settings(base_url: str, api_key: str) -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[arg-type]
        llm_provider="openai",
        llm_model="stub-model",
        llm_api_key=api_key,  # type: ignore[arg-type]
        llm_base_url=base_url,
    )


async def test_round_trip_through_openai_compatible_endpoint(
    stub_endpoint: tuple[str, list[Any]],
) -> None:
    base_url, received = stub_endpoint
    llm = build_llm(_settings(base_url, "test-key"))

    reply = await llm.generate([LLMMessage("system", "be brief"), LLMMessage("user", "hi")])

    assert reply == "hello from stub"
    assert received[0]["model"] == "stub-model"
    assert [m["role"] for m in received[0]["messages"]] == ["system", "user"]


async def test_endpoint_errors_become_llm_error(stub_endpoint: tuple[str, list[Any]]) -> None:
    base_url, _ = stub_endpoint
    llm = build_llm(_settings(base_url, "bad-key"))

    with pytest.raises(LLMError):
        await llm.generate([LLMMessage("user", "hi")])
