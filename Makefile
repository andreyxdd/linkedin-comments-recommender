.PHONY: dev dev-backend dev-frontend build test test-backend test-frontend lint clean setup

# --- Setup ---
setup: ## First-time setup: install dependencies
	cd backend && uv sync --all-extras
	cd frontend && pnpm install
	@[ -f .env ] || cp .env.example .env
	@echo "Done. Edit .env with your API key, then run 'make dev'."

# --- Development ---
dev: ## Start both services with Docker Compose (hot reload)
	docker compose up --build

dev-backend: ## Start backend only (no Docker)
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend: ## Start frontend only (no Docker)
	cd frontend && pnpm dev

# --- Build ---
build: ## Build Docker images
	docker compose build

# --- Test ---
test: ## Run all tests
	cd backend && uv run pytest -v
	cd frontend && pnpm test

test-backend: ## Run backend tests
	cd backend && uv run pytest -v

test-frontend: ## Run frontend tests
	cd frontend && pnpm test

# --- Lint ---
lint: ## Run linters
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && pnpm lint && pnpm tsc --noEmit

lint-fix: ## Fix lint issues
	cd backend && uv run ruff check --fix . && uv run ruff format .
	cd frontend && pnpm lint --fix

# --- Clean ---
clean: ## Remove build artifacts and containers
	docker compose down -v --remove-orphans
	rm -rf backend/.venv frontend/.next frontend/node_modules

# --- Help ---
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
