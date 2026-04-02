# Copilot Instructions — South East Archers

## Build, Test & Lint

Dev/test tooling uses a `Makefile`. App-level commands (user management, scheduling, RBAC) remain as Flask CLI commands.

```bash
# Install all dependencies (Python + Node)
make install

# Run full test suite
make test

# Run a single test file
make test-file FILE=tests/integration/services/test_membership_service.py

# Run tests matching a keyword
make test-k K="test_activate_membership"

# Run tests with coverage report
make test-coverage

# Lint (ruff check + ruff format --check + import-linter)
make lint

# Auto-fix lint/format issues
make lint-fix

# Type checking (mypy)
make typecheck

# Build frontend assets
make assets

# Dev servers (Flask + Vite hot-reload)
make dev

# Clean cache and temporary files
make clean
```

CI runs: `make lint` → `make typecheck` → `make assets` → `make test-coverage` (see `.github/workflows/ci.yml`).

## Architecture

Flask app using a **Routes → Services → Repositories** layered architecture with domain events for side effects.

### Layer rules

| Layer | Role | May import |
|---|---|---|
| **Routes** (`app/routes/`) | HTTP handling, form validation, template rendering | Services, Forms, Models (read-only) |
| **Services** (`app/services/`) | Business logic, orchestration | Repositories, Models, other Services |
| **Repositories** (`app/repositories/`) | Data access (SQLAlchemy queries) | Models, `app.db` |
| **Models** (`app/models/`) | SQLAlchemy model definitions | `app.db` only |

**Routes and Services must NOT import `app.db` directly.** This is enforced by `import-linter` contracts in `pyproject.toml`. All database operations go through repositories that extend `BaseRepository`.

### Domain events (`app/events/`)

Side effects (emails, financial transaction recording) are decoupled from services via blinker signals. Services emit events (e.g., `payment_completed.send(...)`), and handlers in `app/events/handlers.py` react. Add new signals in `app/events/__init__.py` and connect handlers in `connect_handlers()`.

### Frontend

Vite builds assets from `resources/assets/` into `resources/static/`. Templates use Jinja2 with `flask-vite-assets` for asset references. Styling is Tailwind CSS 4; client-side interactivity uses Alpine.js (CSP build).

## Key Conventions

- **Monetary values** are stored in cents (integer) to avoid floating-point issues. Fields are named `amount_cents`, `cost_cents`, etc.
- **Service methods** are `@staticmethod` and return `ServiceResult[T]` (from `app.services.result`). `ServiceResult` is a frozen dataclass with fields `success: bool`, `data: T | None`, `message: str | None`, and `warnings: list[str]`. Use the convenience constructors `ServiceResult.ok(data=..., message=..., warnings=...)` and `ServiceResult.fail(message=..., warnings=...)` instead of building instances directly.
- **Repository methods** are `@staticmethod`. Use `BaseRepository.save()` to commit (handles rollback on failure).
- **RBAC**: Protect routes with `@permission_required("resource.action")` or `@any_permission_required([...])` from `app.utils.decorators`.
- **Testing**: Tests use a real SQLite database (no mocks for DB). Fixtures like `test_user`, `admin_user`, `fake_mailer`, and `fake_queue` are in `tests/conftest.py`. Shared helpers (e.g., `create_user_with_membership`, `assert_email_sent`) are in `tests/helpers.py`.
- **Config**: Three environments — `development`, `testing`, `production` — in `app/config.py`. Tests use `TestingConfig` (SQLite in-memory, CSRF disabled, fast bcrypt rounds).
- **Ruff** is the sole linter/formatter. Line length is 160. Double quotes, space indentation.
