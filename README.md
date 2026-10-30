# Store Support Agent

An AI customer-support agent for small online stores. The goal is an agent that does more than answer FAQs: it looks up orders and shipments, reads the store's policies, and **proposes actions (refunds, exchanges) that a human approves before anything runs**.

> **Status: early.** This repo is being migrated from a thin TypeScript chatbot to a Python agent backend. Today you get a working chat loop end to end. Tools, retrieval, memory and approvals are planned; see [docs/ROADMAP.md](docs/ROADMAP.md).

## What works today

- Chat UI (Next.js) talking to a FastAPI backend, with conversations persisted in Postgres.
- A minimal LangGraph agent (one node) behind a swappable `LLMProvider`.
- A deterministic **fake LLM** so everything runs and tests pass with no API keys.

## What is planned

Tool-calling over a seeded demo store, RAG over policy docs (pgvector), conversation and customer memory, an approval-gated action flow with an audit log, and channel adapters (WhatsApp, Instagram). Details in the roadmap.

## Architecture

```
Browser ──► web/      Next.js UI
              │  /api/chat/*  (rewritten to BACKEND_URL)
              ▼
            backend/  FastAPI
              │  LangGraph agent ──► LLMProvider (fake | openai)
              ▼
            Postgres (+ pgvector)
```

The legacy TypeScript backend inside `web/` (route handlers, Prisma, Redis cache) still works if `BACKEND_URL` is unset. It is being replaced and will be deleted once the Python port is complete.

## Quick start (Windows + WSL2, also fine on Linux/macOS)

Prerequisites:

- WSL2 with Ubuntu. Clone this repo **inside the WSL filesystem** (e.g. `~/code`), not under `/mnt/c`; it is much faster.
- Docker Desktop with WSL integration enabled.
- [`uv`](https://docs.astral.sh/uv/), Node.js 20.9+, and `make`.

```bash
cp backend/.env.example backend/.env
make db-up              # Postgres + pgvector in Docker
make backend-install    # uv sync
make migrate            # create tables
make backend-dev        # API on http://localhost:8000 (docs at /docs)
```

In a second terminal:

```bash
echo 'BACKEND_URL=http://localhost:8000' > web/.env.local
make web-install
make web-dev            # UI on http://localhost:3000
```

Run `make help` for all commands, and `make check` for lint, type-check and tests.

## Data and secrets

All data in this repo is **synthetic**. Do not commit real customer data, API keys, or `.env` files. The default LLM provider is a fake one, so no key is needed to develop or test.

## Layout

```
backend/   Python service (FastAPI, LangGraph, SQLAlchemy, Alembic)
web/       Next.js UI (+ legacy TypeScript backend, being phased out)
docs/      Roadmap and archived notes from the TypeScript era
```

## Contributing

See [AGENTS.md](AGENTS.md) for conventions, commands, and rules (it is written for both humans and AI coding assistants).

## License

[MIT](LICENSE)
