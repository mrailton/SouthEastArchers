.PHONY: help install dev run test test-cov format format-check clean db-upgrade db-migrate shell build assets assets-watch

# Default target
help:
	@echo "South East Archers - Available Commands:"
	@echo ""
	@echo "Setup & Dependencies:"
	@echo "  make install          Install Python and Node.js dependencies"
	@echo "  make install-py       Install Python dependencies only"
	@echo "  make install-node     Install Node.js dependencies only"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Run Flask dev server and watch assets"
	@echo "  make run              Run Flask development server only"
	@echo "  make assets-watch     Watch and rebuild assets on change"
	@echo "  make shell            Open Flask shell"
	@echo ""
	@echo "Building:"
	@echo "  make build            Build production assets"
	@echo "  make assets           Alias for build"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests with pytest"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make test-parallel    Run tests in parallel"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format           Format code with black and isort"
	@echo "  make format-check     Check formatting and code quality"
	@echo ""
	@echo "Database:"
	@echo "  make db-upgrade       Apply database migrations"
	@echo "  make db-migrate       Create new migration (use MSG='description')"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            Remove cache and build files"

# Installation
install: install-py install-node

install-py:
	uv sync

install-node:
	npm ci

# Development
dev:
	@echo "Starting development servers..."
	@trap 'kill 0' INT; \
	npm run dev & \
	uv run flask run --debug

run:
	uv run flask run --debug

shell:
	uv run flask shell

# Assets
build:
	npm run build

assets: build

assets-watch:
	npm run dev

# Testing
test:
	uv run pytest

test-cov:
	uv run pytest --cov=app --cov-report=term-missing

test-parallel:
	uv run pytest -n auto

# Code Quality
format:
	uv run isort app/ tests/
	uv run black app/ tests/

format-check:
	@echo "Checking import order..."
	@uv run isort --check-only app/ tests/
	@echo "Checking code formatting..."
	@uv run black --check app/ tests/
	@echo "Running code quality checks..."
	@uv run flake8 app/ tests/

# Database
db-upgrade:
	uv run flask db upgrade

db-migrate:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Please provide a migration message with MSG='description'"; \
		echo "Example: make db-migrate MSG='add user table'"; \
		exit 1; \
	fi
	uv run flask db migrate -m "$(MSG)"

# Maintenance
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .coverage htmlcov/ dist/ build/
	@echo "Cleaned up cache and build files"
