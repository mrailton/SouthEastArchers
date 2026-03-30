# Copilot Instructions — South East Archers

## Build, Test & Lint

All commands go through Flask's built-in CLI. Use `uv run` to ensure the correct virtualenv:

```bash
# Install all dependencies (Python + Node)
flask install

# Run full test suite
flask test run

# Run a single test file
flask test file tests/services/test_membership_service.py

# Run tests matching a keyword
flask test run -k "test_activate_membership"

# Lint (ruff check + ruff format --check + import-linter)
flask lint all

# Auto-fix lint/format issues
flask lint all --fix

# Type checking (mypy)
flask lint typecheck

# Build frontend assets
flask assets build

# Dev servers (Flask + Vite hot-reload)
flask dev
```

CI runs: `lint check` → `assets build` → `test coverage` (see `.github/workflows/ci.yml`).

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
- **Service methods** are `@staticmethod` and return `tuple[bool, str]` — `(success, message)`.
- **Repository methods** are `@staticmethod`. Use `BaseRepository.save()` to commit (handles rollback on failure).
- **RBAC**: Protect routes with `@permission_required("resource.action")` or `@any_permission_required([...])` from `app.utils.decorators`.
- **Testing**: Tests use a real SQLite database (no mocks for DB). Fixtures like `test_user`, `admin_user`, `fake_mailer`, and `fake_queue` are in `tests/conftest.py`. Shared helpers (e.g., `create_user_with_membership`, `assert_email_sent`) are in `tests/helpers.py`.
- **Config**: Three environments — `development`, `testing`, `production` — in `app/config.py`. Tests use `TestingConfig` (SQLite in-memory, CSRF disabled, fast bcrypt rounds).
- **Ruff** is the sole linter/formatter. Line length is 160. Double quotes, space indentation.
