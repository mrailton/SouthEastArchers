.PHONY: help up down build logs shell manage db-upgrade db-migrate db-downgrade \
       seed test lint lint-fix user-create stats clean

DOCKER_COMPOSE = docker compose
WEB_EXEC = $(DOCKER_COMPOSE) exec web
MANAGE = $(WEB_EXEC) python manage.py

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

up: ## Start all services
	$(DOCKER_COMPOSE) up -d --remove-orphans

up-build: ## Build and start all services
	$(DOCKER_COMPOSE) up -d --build --remove-orphans

down: ## Stop all services
	$(DOCKER_COMPOSE) down --remove-orphans

down-volumes: ## Stop all services and remove volumes
	$(DOCKER_COMPOSE) down -v

build: ## Build all images
	$(DOCKER_COMPOSE) build

logs: ## Tail logs for all services
	$(DOCKER_COMPOSE) logs -f

logs-web: ## Tail logs for the web service
	$(DOCKER_COMPOSE) logs -f web

logs-vite: ## Tail logs for the vite service
	$(DOCKER_COMPOSE) logs -f vite

restart: ## Restart all services
	$(DOCKER_COMPOSE) restart

ps: ## Show running services
	$(DOCKER_COMPOSE) ps

# ---------------------------------------------------------------------------
# Shell access
# ---------------------------------------------------------------------------

shell: ## Open a bash shell in the web container
	$(WEB_EXEC) bash

flask-shell: ## Open a Flask shell with app context
	$(MANAGE) shell

mysql-shell: ## Open a MySQL shell
	$(DOCKER_COMPOSE) exec mysql mysql -u sea_user -psea_password sea_db

redis-cli: ## Open the Redis CLI
	$(DOCKER_COMPOSE) exec redis redis-cli

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

db-upgrade: ## Run database migrations
	$(MANAGE) db upgrade

db-migrate: ## Create a new migration (usage: make db-migrate m="migration message")
	$(MANAGE) db migrate -m "$(m)"

db-downgrade: ## Rollback last migration
	$(MANAGE) db downgrade

db-reset: ## Reset database (WARNING: deletes all data)
	$(MANAGE) db reset

seed: ## Seed roles and permissions
	$(MANAGE) rbac seed

# ---------------------------------------------------------------------------
# Testing & linting
# ---------------------------------------------------------------------------

test: ## Run the test suite
	$(MANAGE) test run

test-verbose: ## Run tests with verbose output
	$(MANAGE) test run -v

test-coverage: ## Run tests with coverage report
	$(MANAGE) test coverage

lint: ## Run lint checks
	$(MANAGE) lint all

lint-fix: ## Auto-fix lint issues
	$(MANAGE) lint fix

typecheck: ## Run mypy type checking
	$(MANAGE) lint typecheck

# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

user-create: ## Create a new user (interactive)
	$(MANAGE) user create

user-create-admin: ## Create a new admin user (interactive)
	$(MANAGE) user create --admin

user-list: ## List all users
	$(MANAGE) user list

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

stats: ## Show application statistics
	$(MANAGE) stats

clean: ## Clean cache and temporary files
	$(MANAGE) clean

# ---------------------------------------------------------------------------
# Manage (catch-all)
# ---------------------------------------------------------------------------

manage: ## Run any manage.py command (usage: make manage cmd="db upgrade")
	$(MANAGE) $(cmd)
