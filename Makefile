.PHONY: help install dev clean test test-parallel test-verbose test-file test-coverage test-k \
       lint lint-fix lint-check format format-check typecheck lint-imports \
       assets assets-watch

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Setup ────────────────────────────────────────────────────────────────────

install: ## Install all dependencies (Python + Node)
	uv sync
	npm ci

dev: ## Run development servers (FastAPI + Vite)
	@mkdir -p resources/static
	@if [ ! -e resources/static/images ]; then ln -s ../assets/images resources/static/images; fi
	@echo "Starting development servers..."
	@echo "  - Vite dev server (asset hot reloading)"
	@echo "  - FastAPI dev server (uvicorn)"
	@echo ""
	@echo "Press Ctrl+C to stop"
	@echo ""
	@trap 'kill 0' EXIT; \
		npm run dev & \
		uv run uvicorn asgi:app --reload --host 127.0.0.1 --port 8000 & \
		wait

clean: ## Remove cache and temporary files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
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

