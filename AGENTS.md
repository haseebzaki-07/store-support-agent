# AGENTS.md

Guidance for AI coding assistants and contributors working in this repo.

## What this project is

A store support agent: it answers customer questions, looks up orders, reads policy documents, and **proposes** actions (refund, exchange) that a human approves. Early stage: the Python backend is being built; see `docs/ROADMAP.md` for what exists and what is planned.

## Layout

- `backend/` Python 3.12+ service. Package: `backend/src/chatbot/`.
  - `api/` HTTP routes · `services/` business logic · `agent/` LangGraph graph · `llm/` provider interface (+ fake) · `models.py` SQLAlchemy · `schemas.py` API schemas · `migrations/` Alembic
- `web/` Next.js UI. It also contains a **legacy TypeScript backend** (`app/api/chat`, `lib/llm.ts`, `lib/tools`, `lib/services`, `lib/redis.ts`, `prisma/`) that is being replaced. Do not extend it; port behavior to `backend/` instead.
- `docs/` roadmap and archived docs from the TypeScript era.

## Commands (run from the repo root)

| Command | What it does |
|---|---|
| `make db-up` / `make db-down` | start / stop Postgres (pgvector) in Docker |
| `make backend-install` | `uv sync` |
| `make migrate` | apply Alembic migrations |
| `make backend-dev` | run the API on :8000 |
| `make backend-test` | pytest (needs Postgres from `make db-up`) |
| `make backend-lint` / `make backend-format` | ruff check+format check / fix |
| `make backend-typecheck` | pyright |
| `make check` | lint + typecheck + tests |
| `make web-install` / `make web-dev` | install / run the UI |

## Conventions

- Python 3.12+, full type hints. `make check` must pass before a change is done.
- Async SQLAlchemy 2.x. Schema changes only through Alembic: `cd backend && uv run alembic revision --autogenerate -m "message"`, then review the generated file.
- The API is camelCase JSON and is consumed by `web/app/page.tsx` (`POST /api/chat/message`, `GET /api/chat/message?sessionId=`). Do not change the contract without updating the UI.
- Talk to LLMs only through `LLMProvider` (`backend/src/chatbot/llm/`). Tests use `FakeLLM`; **never call a real LLM API from tests**.
- Stay vendor-neutral: never import a vendor SDK outside `llm/`. Providers are chosen by `LLM_PROVIDER`/`LLM_MODEL`/`LLM_BASE_URL`; per-provider argument mapping lives in `llm/langchain_provider.py`, and each provider's package is an optional extra in `pyproject.toml`. The same pattern applies to embeddings (planned, T2.1).
- Anything that changes business state (refund, exchange, cancel) must go through the approval flow (planned). The agent proposes; a human approves. Never execute such actions directly from the agent.
- Add or update tests with every behavior change. Keep commits small and focused.

## Rules

- No secrets and no real customer data anywhere in the repo, tests, fixtures or prompts. All data is synthetic. Use `.env` files (git-ignored) for local settings; only commit `*.example`.
- Do not hard-code store policy in prompts; policy belongs in `backend/data/` documents (retrieval is planned).
- Leave `TODO(...)` comments only for work that is genuinely planned, tagged with the task id from `docs/ROADMAP.md` (e.g. `TODO(T1.4)`).
- This is an application. Do not add model training, fine-tuning, or LLM evaluation tooling.
