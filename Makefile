.PHONY: help up down build rebuild restart logs web-logs \
       shell flask-shell test test-file test-k lint lint-fix typecheck \
       migrate migration db-reset seed mysql clean status install create-user \
       create-admin stats

COMPOSE = docker compose
WEB     = $(COMPOSE) exec web
MYSQL   = $(COMPOSE) exec mysql

help: ## Show available commands
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Docker ──────────────────────────────────────────────

up: ## Start all services
	$(COMPOSE) up -d --remove-orphans

down: ## Stop all services
	$(COMPOSE) down --remove-orphans

build: ## Build images
	$(COMPOSE) build

rebuild: ## Rebuild images and restart
	$(COMPOSE) up -d --build

restart: ## Restart all services
	$(COMPOSE) restart

logs: ## Follow logs (all services)
	$(COMPOSE) logs -f

web-logs: ## Follow web container logs
	$(COMPOSE) logs -f web

status: ## Show container status
	$(COMPOSE) ps

clean: ## Stop and remove containers, volumes, and images
	$(COMPOSE) down -v --rmi local

# ── Shell ───────────────────────────────────────────────

shell: ## Open bash in web container
	$(WEB) bash

flask-shell: ## Open Flask interactive shell
	$(WEB) flask shell

mysql: ## Open MySQL shell
	$(MYSQL) mysql -u sea_user -psea_password sea_db

# ── Testing ─────────────────────────────────────────────

test: ## Run full test suite
	$(WEB) python manage.py test run

test-file: ## Run specific test file (FILE=tests/path.py)
	$(WEB) python manage.py test file $(FILE)

test-k: ## Run tests by keyword (K=keyword)
	$(WEB) python manage.py test run -k "$(K)"

test-cov: ## Run tests with coverage report
	$(WEB) python manage.py test coverage

# ── Code Quality ────────────────────────────────────────

lint: ## Run all linting checks
	$(WEB) python manage.py lint all

lint-fix: ## Auto-fix lint and format issues
	$(WEB) python manage.py lint all --fix

typecheck: ## Run mypy type checking
	$(WEB) python manage.py lint typecheck

# ── Database ────────────────────────────────────────────

migrate: ## Apply pending migrations
	$(WEB) python manage.py db upgrade

migration: ## Create new migration (MSG="description")
	$(WEB) python manage.py db migrate -m "$(MSG)"

db-reset: ## Reset database (drops all tables)
	$(WEB) python manage.py db reset

seed: ## Seed RBAC roles and permissions
	$(WEB) python manage.py rbac seed

# ── Dependencies ────────────────────────────────────────

install: ## Sync Python dependencies inside web container
	$(WEB) uv pip install --system -r pyproject.toml --group dev

# ── Utilities ───────────────────────────────────────────

create-user: ## Create a new user interactively
	$(WEB) python manage.py user create

create-admin: ## Create new admin user
	$(WEB) python manage.py user create --admin

stats: ## Show application statistics
	$(WEB) python manage.py stats
