.PHONY: help install setup dev server clean test test-parallel test-verbose test-file test-coverage test-k \
       lint lint-fix lint-check format format-check typecheck lint-imports \
       assets assets-watch db-upgrade rbac-seed

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Setup ────────────────────────────────────────────────────────────────────

install: ## Install all dependencies (Python + Node)
	uv sync
	npm ci

setup: ## First-time setup: install deps and build assets
	$(MAKE) install
	$(MAKE) assets

dev: ## Run dev server and watch assets (parallel)
	@$(MAKE) -j2 server assets-watch

server: ## Run FastAPI with reload
	uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

clean: ## Remove cache and temporary files
	rm -rf app/resources/static/dist
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .import_linter_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

# ── Testing ──────────────────────────────────────────────────────────────────

test: ## Run test suite
	uv run pytest

test-parallel: ## Run test suite in parallel (faster on multi-core machines)
	uv run pytest -n auto

test-verbose: ## Run test suite with verbose output
	uv run pytest -v

test-file: ## Run a single test file (FILE=tests/path/to/test.py)
	uv run pytest $(FILE)

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=app --cov-report=term-missing --cov-report=html --no-cov-on-fail

test-k: ## Run tests matching keyword (K="test_something")
	uv run pytest -k "$(K)"

# ── Linting ──────────────────────────────────────────────────────────────────

lint: ## Run all quality checks (ruff + format + import boundaries)
	uv run ruff check app/ tests/
	uv run ruff format --check app/ tests/
	uv run lint-imports

lint-fix: ## Auto-fix all lint and formatting issues
	uv run ruff check --fix app/ tests/
	uv run ruff format app/ tests/
	uv run lint-imports

lint-check: ## Run ruff linting and format checks only
	uv run ruff check app/ tests/
	uv run ruff format --check app/ tests/

format: ## Format code with ruff
	uv run ruff format app/ tests/

format-check: ## Check code formatting without modifying
	uv run ruff format --check app/ tests/

typecheck: ## Run mypy type checking
	uv run mypy app/

lint-imports: ## Check module boundary contracts
	uv run lint-imports

# ── Assets ───────────────────────────────────────────────────────────────────

assets: ## Build production assets with Vite
	npm run build

assets-watch: ## Watch and rebuild assets on change
	npm run dev

db-upgrade: ## Apply database migrations
	uv run sea db upgrade

rbac-seed: ## Seed default roles and permissions
	uv run sea rbac seed

