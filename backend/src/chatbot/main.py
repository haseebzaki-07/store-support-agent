from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from chatbot.agent import build_graph
from chatbot.api import chat, health
from chatbot.config import Settings, get_settings
from chatbot.db import create_engine, create_session_factory
from chatbot.errors import register_error_handlers
from chatbot.llm import build_llm


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    engine = create_engine(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.graph = build_graph(build_llm(settings))
    try:
        yield
    finally:
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Store Support Agent", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings or get_settings()
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(chat.router)
    # TODO(security): add auth and per-session rate limiting before exposing this publicly.
    return app


app = create_app()
