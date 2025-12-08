.PHONY: help install dev run test test-cov format format-check clean db-upgrade db-migrate shell build assets assets-watch docker-up docker-down docker-logs docker-rebuild docker-prod-up docker-prod-down

# Docker Compose files
DOCKER_DEV_COMPOSE = docker-compose -f docker/docker-compose.dev.yml
DOCKER_PROD_COMPOSE = docker-compose -f docker/docker-compose.yml

# Default target
help:
	@echo "South East Archers - Available Commands:"
	@echo ""
	@echo "Docker Development (Recommended):"
	@echo "  make docker-up        Start all services with Docker Compose (dev)"
	@echo "  make docker-down      Stop all Docker services"
	@echo "  make docker-logs      Follow logs from all services"
	@echo "  make docker-rebuild   Rebuild and restart Docker services"
	@echo "  make docker-shell     Open shell in web container"
	@echo "  make docker-db-shell  Open MySQL shell in database container"
	@echo ""
	@echo "Docker Production:"
	@echo "  make docker-prod-up   Start production stack with Docker Compose"
	@echo "  make docker-prod-down Stop production stack"
	@echo ""
	@echo "Local Development (Without Docker):"
	@echo "  make install          Install Python and Node.js dependencies"
	@echo "  make dev              Run Flask dev server and watch assets"
	@echo "  make run              Run Flask development server only"
	@echo "  make worker-dev       Start RQ worker with auto-reload"
	@echo "  make shell            Open Flask shell"
	@echo ""
	@echo "Building:"
	@echo "  make build            Build production assets"
	@echo "  make assets           Alias for build"
	@echo "  make assets-watch     Watch and rebuild assets on change"
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

# Docker Development Commands
docker-up:
	@echo "🚀 Starting development environment with Docker Compose..."
	$(DOCKER_DEV_COMPOSE) up -d
	@echo ""
	@echo "✅ Services started!"
	@echo "   Web:      http://localhost:5000"
	@echo "   Mailhog:  http://localhost:8025"
	@echo ""
	@echo "📝 View logs: make docker-logs"

docker-down:
	@echo "🛑 Stopping all services..."
	$(DOCKER_DEV_COMPOSE) down

docker-logs:
	$(DOCKER_DEV_COMPOSE) logs -f

docker-rebuild:
	@echo "🔨 Rebuilding and restarting services..."
	$(DOCKER_DEV_COMPOSE) up -d --build

docker-shell:
	$(DOCKER_DEV_COMPOSE) exec web /bin/bash

docker-db-shell:
	$(DOCKER_DEV_COMPOSE) exec db mysql -udevuser -pdevpassword southeastarchers

# Docker Production Commands
docker-prod-up:
	@echo "🚀 Starting production environment..."
	$(DOCKER_PROD_COMPOSE) up -d
	@echo "✅ Production services started!"

docker-prod-down:
	$(DOCKER_PROD_COMPOSE) down

# Local Installation (without Docker)
install: install-py install-node

install-py:
	uv sync

install-node:
	npm ci

# Local Development (without Docker)
dev:
	@echo "Starting development servers..."
	@trap 'kill 0' INT; \
	npm run dev & \
	watchmedo auto-restart --directory=./app --pattern=*.py --recursive -- uv run python worker.py & \
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

# Background Jobs
worker:
	uv run python worker.py

worker-dev:
	@echo "Starting RQ worker with auto-reload..."
	@watchmedo auto-restart --directory=./app --pattern=*.py --recursive -- uv run python worker.py

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
