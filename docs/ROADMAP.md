# Roadmap

Legend: `[x]` done, `[ ]` planned. Items are intentionally small so each can be built and reviewed on its own.

## Phase 0: Foundations

- [x] Monorepo layout (`web/` + `backend/`), MIT license, README, AGENTS.md
- [x] FastAPI backend with Postgres (async SQLAlchemy + Alembic)
- [x] `LLMProvider` interface with a deterministic `FakeLLM`
- [x] Minimal LangGraph graph (single node)
- [x] Chat API compatible with the existing UI contract
- [x] pytest, ruff, pyright, GitHub Actions CI, `docker compose` Postgres
- [ ] Synthetic demo store: seed script (products, customers, orders, shipments)
- [ ] Policy documents in `backend/data/policies/` (returns, shipping, warranty)
- [ ] Real LLM provider (`OpenAIProvider`): timeouts, retries, error mapping
- [ ] Remove the legacy TypeScript backend from `web/` (route handlers, Prisma, Redis cache) once the above is verified
- [ ] Fix `web/package-lock.json` (out of sync with `package.json`, so `npm ci` fails) and add a web CI job (typecheck)
- [ ] Add a readiness check (`/health/ready`) that verifies the database connection

## Phase 1: Agent core (tools)

- [ ] Tool interface and registry
- [ ] Order lookup, shipment tracking, inventory check tools against seeded tables
- [ ] Tool-calling loop in the LangGraph graph with result validation and fallbacks
- [ ] Per-turn timeout and structured error handling
- [ ] Streaming responses to the UI

## Phase 2: Knowledge (RAG)

- [ ] Document ingestion and chunking
- [ ] pgvector embeddings; hybrid (keyword + vector) retrieval
- [ ] Answers with citations to policy documents
- [ ] "Not in the docs" handling that hands off instead of guessing

## Phase 3: Memory

- [ ] Rolling conversation summaries
- [ ] Customer facts with explicit consent
- [ ] Delete-on-request for stored memory

## Phase 4: Approval-gated actions

- [ ] `action_proposals` and `approvals` tables, plus an audit log
- [ ] Agent proposes refund / exchange; graph pauses (LangGraph interrupt + Postgres checkpointer)
- [ ] Minimal reviewer UI: approve / reject with a reason
- [ ] Idempotent execution of approved actions

## Phase 5: Channels, safety, operations

- [ ] WhatsApp and Instagram adapters with webhook signature verification
- [ ] Human handoff
- [ ] Prompt-injection defenses, input limits, per-session rate limits
- [ ] Tracing / observability
- [ ] Optional: expose the tools as an MCP server
