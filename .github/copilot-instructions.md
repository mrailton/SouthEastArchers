# Copilot Instructions — South East Archers

## Build, Test & Lint

Dev/test tooling uses a `Makefile`. App-level commands use the Click CLI in `app/cli/`.

```bash
make install
make test
make test-file FILE=tests/unit/services/test_membership_service.py
make test-k K="test_activate_membership"
make test-coverage
make lint
make lint-fix
make typecheck
make assets
make dev
make clean
```

CI runs: `make lint` → `make typecheck` → `make assets` → `make test-coverage`.

## Architecture

FastAPI app using **Routes → Services → Repositories** with domain events for side effects.

| Layer | Role | May import |
|---|---|---|
| **Routes** (`app/routes/`) | HTTP handling, form validation, templates | Services, schemas/forms, policies |
| **Services** (`app/services/`) | Business logic, orchestration | Repositories, models, other services |
| **Repositories** (`app/repositories/`) | Data access | Models, `app.db` |
| **Models** (`app/models/`) | SQLAlchemy definitions | `app.db` |

### Domain events (`app/events/`)

Side effects (emails, financial transactions) are decoupled via blinker signals. Services emit events; handlers in `app/events/handlers.py` react. Handlers are connected in `app/main.py` lifespan via `connect_handlers()`.

### Frontend

Vite builds `app/resources/static/js/{site,admin}.js` into `app/resources/static/dist/assets/`. Layout templates load `/static/assets/site.css` and `/static/assets/site.js` (or `admin.*` for admin pages). Raw static files (e.g. images) are served from `app/resources/static/`. Templates live in `app/resources/templates/` and are rendered via `app/templating.py`. Styling is Tailwind CSS 4; interactivity uses Alpine.js.

## Key Conventions

- Monetary values are stored in **cents** (integer).
- Service methods return `ServiceResult[T]` from `app.services.result`.
- Repository methods extend `BaseRepository` for commits/rollbacks.
- RBAC: protect admin routes with `require_perms(...)` from `app/routes/admin/_helpers.py`.
- Admin forms use WTForms (`app/forms/`); auth/member forms use Pydantic (`app/schemas/forms.py`).
- CSRF: session token via `get_csrf_token()`; verify on POST with `verify_csrf()`.
- Testing: SQLite in-memory DB, FastAPI `TestClient` with `CSRFClient` wrapper, fixtures in `tests/conftest.py`. HTTP route tests live in `tests/feature/` and should only assert HTTP behaviour (status, redirect, flash, permissions) — business logic belongs in `tests/unit/`. Helpers in `tests/http_helpers.py`.
- Config: Pydantic `Settings` in `app/core/config.py` (environments: `development`, `testing`, `production`).
- Ruff is the linter/formatter (line length 160).
