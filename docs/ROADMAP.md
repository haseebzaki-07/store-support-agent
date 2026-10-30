# Roadmap

Each task is sized for one focused working session: a single feature with tests that can be built, run, and reviewed on its own. Tasks have ids (`T1.4`) that match the `TODO(...)` tags in the code.

- **Done when** is the acceptance check. Every task also needs `make check` to pass and tests for any behavior it adds.
- **Needs** lists prerequisite tasks when it isn't obvious from the phase order.
- Suggested order: finish Phase 0 first (later phases need the seed data and policy documents), then go phase by phase.

## Scope guardrails

- All data is synthetic. No real customer data, no real API keys, in code, tests, fixtures or prompts.
- The agent **proposes**, a human **approves**. Nothing that changes business state runs without approval.
- Vendor neutral: models and embeddings are reached through our own interfaces and chosen by configuration.
- This is an application. It does not include model training, fine-tuning, or LLM evaluation tooling. Tests use the fake LLM.

## Done

- [x] Monorepo layout (`web/` + `backend/`), MIT license, README, AGENTS.md
- [x] FastAPI backend, async SQLAlchemy + Alembic, chat API compatible with the existing UI
- [x] Minimal LangGraph graph (single node)
- [x] Platform-independent `LLMProvider`: fake (default), OpenAI and any OpenAI-compatible server, Anthropic, Gemini, Ollama
- [x] pytest, ruff, pyright, `docker compose` Postgres, GitHub Actions CI

## Phase 0: Foundations

### T0.1 Synthetic demo store
**Build:** Alembic migration for `products`, `customers`, `orders`, `order_items`, `shipments`, and a seed script (`make seed`) that loads about 20 products, 10 customers and 30 orders in varied states (placed, shipped, delivered, delayed, returned). Emails use `@example.test`; names are obviously fake.
**Done when:** `make seed` is idempotent (running it twice leaves the same row counts), the seeder has tests, and every order status above is represented.

### T0.2 Policy documents
**Build:** Markdown policy documents under `backend/data/policies/` (returns, shipping, warranty, payments, FAQ) written for the fictional store, plus a loader that returns them with their paths and titles. Remove the policy text hard-coded in `prompts.py`.
**Done when:** the loader has tests, and the system prompt no longer contains policy facts.

### T0.3 Cleanup and CI for the web app
**Build:** Delete the legacy TypeScript backend in `web/` (`app/api/chat`, `lib/llm.ts`, `lib/tools`, `lib/services`, `lib/redis.ts`, `prisma/`, and their dependencies), make `BACKEND_URL` required, fix `web/package-lock.json`, add a web job (typecheck) to CI, and add `/health/ready` that checks the database connection.
**Done when:** `npm ci` works, CI runs both jobs, the UI chats through the Python backend only, and `/health/ready` returns 503 when the database is down (tested).

## Phase 1: Agent core (tools)

### T1.1 Tool interface and registry
**Build:** A `Tool` abstraction with typed (pydantic) arguments and results, a registry, and JSON-schema export for model tool-calling. Tools get a database session injected.
**Done when:** a sample tool can be registered, validated, and invoked by name; invalid arguments return a structured error rather than raising; tests cover both.

### T1.2 Order and shipment tools
**Build:** Read-only `lookup_order` and `track_shipment` tools over the seeded tables. Lookups require the order id plus the customer's email, so an order id alone reveals nothing.
**Needs:** T0.1, T1.1
**Done when:** tests cover found, not found, and wrong-email cases, and none of them leak whether an order exists for another customer.

### T1.3 Inventory and product search tools
**Build:** `check_inventory` and `search_products` (name/category match) over the seeded products.
**Needs:** T0.1, T1.1
**Done when:** tests cover in stock, out of stock, unknown product, and an ambiguous search.

### T1.4 Tool calling in the agent loop
**Build:** Extend `LLMProvider` so a response can be text or tool calls, run a tool-calling loop in the LangGraph graph with a maximum iteration count, and feed tool results back to the model.
**Needs:** T1.1, T1.2
**Done when:** a scripted fake LLM that requests a tool call produces the expected final reply in a test; hitting the iteration limit ends the turn with a safe message; the OpenAI-compatible stub-server test also covers a tool call.

### T1.5 Reliability: timeouts, retries, fallbacks
**Build:** Per-turn deadline, per-tool timeout, bounded retries with backoff for provider errors, validation of tool results, and a friendly fallback reply when the model or a tool fails. Never return an empty reply.
**Needs:** T1.4
**Done when:** tests simulate a slow model, a failing model, and a failing tool, and each ends with a fallback reply and a stored conversation.

### T1.6 Streaming responses
**Build:** A server-sent-events endpoint that streams the reply, and the UI changes to render it incrementally. Keep the existing non-streaming endpoint working.
**Needs:** T1.4
**Done when:** a test reads the stream and reassembles the same text as the non-streaming call; the UI shows text as it arrives; a dropped connection does not leave a half-saved message.

## Phase 2: Knowledge (RAG)

### T2.1 Embedding provider interface
**Build:** An `EmbeddingProvider` interface mirroring `LLMProvider`: a deterministic fake (default) plus the same set of providers by configuration (`EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`).
**Done when:** the fake returns stable vectors of a fixed dimension, provider settings are validated like the LLM ones, and there is a stub-server test for OpenAI-compatible embeddings.

### T2.2 Ingestion and pgvector storage
**Build:** Chunk the policy documents, embed them, and store chunks with embeddings in Postgres (pgvector) via a migration; a `make ingest` command that is safe to re-run.
**Needs:** T0.2, T2.1
**Done when:** re-ingesting an unchanged document creates no duplicates, a changed document replaces its chunks, and tests check chunk boundaries and the stored dimension.

### T2.3 Hybrid retrieval
**Build:** Combine Postgres full-text search with vector similarity and merge the rankings (reciprocal rank fusion). Return chunks with scores and source metadata.
**Needs:** T2.2
**Done when:** tests show a keyword-only query (an exact term) and a paraphrased query each retrieve the right policy chunk.

### T2.4 Grounded answers with citations
**Build:** A retrieval node in the graph; answers use retrieved chunks and name their source documents; the API returns the citations with the reply.
**Needs:** T2.3
**Done when:** a test asserts that a policy question returns a reply plus the expected source, and the UI shows the sources.

### T2.5 Out-of-scope handling
**Build:** When retrieval finds nothing relevant, the agent says it does not know and offers to hand off to a person instead of guessing.
**Needs:** T2.4
**Done when:** tests cover a question the documents cannot answer, and the reply neither invents policy nor claims certainty.

## Phase 3: Memory

### T3.1 Rolling conversation summaries
**Build:** Summarize older messages once a conversation grows past the history window, store the summary, and include it as context instead of dropping old turns.
**Done when:** a long scripted conversation keeps a stable context size, and a fact from early in the conversation is still available later (tested with the fake LLM).

### T3.2 Customer memory with consent and deletion
**Build:** Store customer preferences as facts only after explicit consent, with a way to list and delete them (API plus tests). Honor deletion everywhere the facts are used.
**Done when:** nothing is stored without consent, deleted facts no longer appear in context, and tests cover consent, listing and deletion.

## Phase 4: Approval-gated actions

### T4.1 Action data model and audit log
**Build:** Tables and migration for `action_proposals`, `approvals` and an append-only `audit_log`; models and a small service for creating and reading them.
**Done when:** every state change writes an audit row, and a test proves audit rows cannot be updated through the service.

### T4.2 Propose-refund tool with graph interrupt
**Build:** A `propose_refund` tool that creates a proposal (never a refund) and pauses the graph using LangGraph `interrupt` with a Postgres checkpointer, so the conversation resumes after review.
**Needs:** T4.1, T1.4
**Done when:** a test runs: customer asks for a refund, a proposal appears, the graph is paused, and no refund exists yet.

### T4.3 Reviewer API
**Build:** Endpoints to list pending proposals and to approve or reject with a reason; approving or rejecting resumes the paused conversation.
**Needs:** T4.2
**Done when:** tests cover approve, reject, double-decision (rejected with a clear error), and unknown proposal.

### T4.4 Reviewer UI
**Build:** A minimal page in `web/` listing pending proposals with the conversation context and approve/reject controls.
**Needs:** T4.3
**Done when:** a reviewer can approve a proposal from the UI and the customer's chat receives the follow-up.

### T4.5 Idempotent execution of approved actions
**Build:** Execute an approved refund against the seeded order exactly once, even if the approval is submitted twice or the worker retries.
**Needs:** T4.3
**Done when:** tests prove double submission and a simulated crash-and-retry both result in exactly one refund and a complete audit trail.

## Phase 5: Channels, safety, operations

### T5.1 Channel adapters (WhatsApp first)
**Build:** Replace the web-only path with a channel interface; implement WhatsApp webhook verification (signature check) and message handling through the same chat service. Instagram follows the same pattern.
**Done when:** tests cover valid and invalid signatures, and a WhatsApp-style payload produces a reply through the shared service.

### T5.2 Human handoff
**Build:** A handoff state on a conversation: the agent stops replying, the conversation is flagged for a person, and a person can reply or return it to the agent.
**Done when:** tests cover the full cycle (agent, handoff, human reply, back to agent) and that the agent stays silent during handoff.

### T5.3 Security hardening
**Build:** Prompt-injection defenses (treat retrieved text and tool output as data, not instructions), input size limits, per-session rate limiting, and authentication for the reviewer endpoints.
**Done when:** tests include injection attempts inside a policy document and inside a user message, and neither can trigger an unapproved action; rate-limited requests return 429; reviewer endpoints reject unauthenticated calls.

### T5.4 Observability
**Build:** Request ids, structured logs, and tracing of each turn (model calls, tool calls, retrieval) behind a vendor-neutral interface, with the exporter chosen by configuration.
**Done when:** a turn produces a trace with spans for model, tools and retrieval, and logs never contain secrets or message bodies (tested).

### T5.5 MCP server for the tools
**Build:** Expose the read-only tools through an MCP server so other agents and IDEs can use them.
**Needs:** T1.1
**Done when:** an MCP client test lists the tools and calls one successfully; write actions are not exposed.
