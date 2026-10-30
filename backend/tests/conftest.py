"""Test fixtures. Tests run against a real Postgres (see `make db-up`), never a real LLM."""

import os
from collections.abc import AsyncIterator

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from chatbot import models  # noqa: F401  (registers tables on Base.metadata)
from chatbot.config import Settings
from chatbot.db import Base
from chatbot.main import create_app

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://chatbot:chatbot@localhost:5432/chatbot_test"
)


async def _ensure_database_exists(url: str) -> None:
    parsed = make_url(url)
    conn = await asyncpg.connect(
        host=parsed.host,
        port=parsed.port,
        user=parsed.username,
        password=parsed.password,
        database="postgres",
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", parsed.database
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{parsed.database}"')
    finally:
        await conn.close()


@pytest.fixture
async def db_url() -> AsyncIterator[str]:
    """A clean schema in the test database for every test."""
    await _ensure_database_exists(TEST_DATABASE_URL)
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    yield TEST_DATABASE_URL


@pytest.fixture
async def client(db_url: str) -> AsyncIterator[AsyncClient]:
    app = create_app(Settings(database_url=db_url, llm_provider="fake"))
    # httpx's ASGITransport does not run lifespan events, so enter the lifespan explicitly.
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client,
    ):
        yield http_client
