.DEFAULT_GOAL := help

.PHONY: help db-up db-down backend-install backend-dev backend-test backend-lint \
	backend-format backend-typecheck migrate web-install web-dev check

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

db-up: ## Start Postgres (pgvector) in Docker
	docker compose up -d --wait db

db-down: ## Stop Postgres (data is kept in a Docker volume)
	docker compose down

backend-install: ## Install backend deps (add EXTRAS="--extra anthropic" for a model provider)
	cd backend && uv sync $(EXTRAS)

backend-dev: ## Run the API on http://localhost:8000
	cd backend && uv run uvicorn chatbot.main:app --reload --port 8000

migrate: ## Apply database migrations
	cd backend && uv run alembic upgrade head

backend-test: ## Run backend tests (needs `make db-up`)
	cd backend && uv run pytest

backend-lint: ## Ruff lint + format check
	cd backend && uv run ruff check . && uv run ruff format --check .

backend-format: ## Auto-fix lint issues and format
	cd backend && uv run ruff check --fix . && uv run ruff format .

backend-typecheck: ## Pyright
	cd backend && uv run pyright

web-install: ## Install web dependencies
	cd web && npm install

web-dev: ## Run the UI on http://localhost:3000
	cd web && npm run dev

check: backend-lint backend-typecheck backend-test ## Lint, type-check and test the backend
