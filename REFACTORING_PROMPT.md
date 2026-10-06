# FastAPI Architecture Refactoring Prompt

You are refactoring a FastAPI application from an over-engineered architecture to a cleaner, simpler one optimized for small personal projects.

## Current Architecture Issues

- The app uses a custom domain event system with blinker signals and deferred background handlers
- Database sessions are managed via context variables instead of dependency injection
- Too many layers (policies, RBAC, event handlers) for a small project
- The bootstrap code is ~95 lines of complex setup

## Target Architecture

### Keep These Patterns

- SQLAlchemy ORM with Alembic migrations (unchanged)
- Pydantic settings (unchanged)
- Service layer for business logic (unchanged)
- Repository pattern for data access (unchanged)
- Import linting contracts to maintain clean module boundaries (keep but simplify)
- CLI commands (unchanged, but simplify session handling)
- Tests (unchanged)

### Replace These Patterns

- Remove the entire `app/events/` directory and all event dispatch/signal listening
- Remove custom database session context variable management (`_current_session`, `set_current_session`, etc.)
- Replace all database session handling with FastAPI dependency injection (`Depends(get_db)`)
- Remove the deferred background handler system and context variable queueing
- Remove RBAC, policies, and permission layers from the base (these can be added per-project if needed)
- Remove the `_error_page_db_session()` context manager complexity

## Specific Refactoring Tasks

### Task 1: Simplify Database Session Management

**What to do:**

- Keep `app/db.py` but remove context variable logic
- Update `get_current_session()` pattern to use FastAPI `Depends(get_db)` dependency injection
- All routes should accept `db: Session = Depends(get_db)` as a parameter
- All services/repositories should accept `db: Session` as a constructor or method parameter
- Remove `set_current_session()`, `reset_current_session()`, and `_current_session` context variable

**Target result:**

`app/db.py` should have:
- `Base` declarative base
- `engine` creation
- `SessionLocal` session factory
- Simple `init_db()` function

No context variables, no global session management.

### Task 2: Create/Update Core Dependencies

**What to do:**

- Create or update `app/core/dependencies.py` with a simple `get_db()` dependency
- This dependency should yield a session and close it after the request

**Example target:**

```python
from collections.abc import Generator
from sqlalchemy.orm import Session
from app.db import SessionLocal

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Task 3: Replace Event System with Direct Service Calls

**What to do:**

- Delete `app/events/` directory entirely
- Find all places where events are dispatched (e.g., `user_registered.send(...)`, `payment_completed.send(...)`)
- Replace with direct service calls inline in the route handler or service
- If async side-effects are needed later, use FastAPI's `BackgroundTasks` (add on-demand)
- Remove all event handler registration code from `main.py` lifespan

**Example transformation:**

From:
```python
def complete_payment(self, payment_id: int):
    payment = self.repo.get(payment_id)
    payment.mark_completed()
    self.db.commit()
    payment_completed.send(self, user_id=payment.user_id, payment_id=payment_id)
```

To:
```python
def complete_payment(self, payment_id: int):
    payment = self.repo.get(payment_id)
    payment.mark_completed()
    self.db.commit()
    mail.send_payment_receipt(payment.user_id, payment_id)
    finance.record_transactions(payment_id)
```

### Task 4: Simplify main.py

**What to do:**

- Remove the complex lifespan context manager
- Remove event handler registration and connection
- Remove custom middleware for deferred event handler execution
- Remove the `_error_page_db_session()` and related error page session management
- Keep SessionMiddleware, router includes, and basic exception handlers only
- Target: ~30 lines instead of ~95

**Target result:**

```python
from fastapi import FastAPI
from fastapi.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.routes import api_router

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=settings.session_max_age_seconds,
    https_only=settings.session_secure_cookie,
    same_site=settings.session_same_site,
)

app.include_router(api_router)

# Optional: Keep only essential exception handlers
@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, exc: LoginRequired):
    return RedirectResponse(url="/auth/login", status_code=303)
```

### Task 5: Update All Route Handlers

**What to do:**

- Change from pulling session via `get_current_session()` to accepting `db: Session = Depends(get_db)`
- Pass `db` explicitly to services and repositories
- Remove any direct session manipulation or context variable access

**Example transformation:**

From:
```python
@router.get("/users/{user_id}")
async def get_user(user_id: int):
    db = get_current_session()
    user = UserRepository(db).get_by_id(user_id)
    return user
```

To:
```python
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = UserRepository(db).get_by_id(user_id)
    return user
```

### Task 6: Update All Services

**What to do:**

- Accept `db: Session` as a parameter to the service methods or constructor
- Remove any calls to `get_current_session()`
- Pass `db` to repositories explicitly

**Example transformation:**

From:
```python
class UserService:
    def create_user(self, name: str, email: str):
        db = get_current_session()
        repo = UserRepository(db)
        user = repo.create(name, email)
        db.commit()
        return user
```

To:
```python
class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)
    
    def create_user(self, name: str, email: str):
        user = self.repo.create(name, email)
        self.db.commit()
        return user
```

Or alternatively, accept db per method:

```python
class UserService:
    def create_user(self, db: Session, name: str, email: str):
        repo = UserRepository(db)
        user = repo.create(name, email)
        db.commit()
        return user
```

### Task 7: Update All Repositories

**What to do:**

- Accept `db: Session` in the constructor
- No changes to query logic, just session management
- Ensure all repositories follow the same pattern

**Example target:**

```python
class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create(self, name: str, email: str):
        user = User(name=name, email=email)
        self.db.add(user)
        return user
```

### Task 8: Update CLI Commands

**What to do:**

- Replace manual session context management (`_open_cli_session`, `_close_cli_session`) with a simpler pattern
- Use dependency injection where possible, or simple direct session creation for CLI
- Remove calls to `flush_deferred_handlers()` (the deferred system is gone)
- Remove event handler connection from CLI bootstrap

**Example transformation:**

From:
```python
def _open_cli_session() -> tuple[Session | None, Token | None]:
    try:
        get_current_session()
        return None, None
    except RuntimeError:
        session = db.create_session()
        token = set_current_session(session)
        return session, token

@cli.command()
def users_create() -> None:
    session, token = _open_cli_session()
    try:
        # ... do work ...
    finally:
        _close_cli_session(session, token)
```

To:
```python
@cli.command()
def users_create() -> None:
    db_session = db.SessionLocal()
    try:
        # ... do work with db_session ...
        db_session.commit()
    finally:
        db_session.close()
```

### Task 9: Simplify Import Linting Contracts

**What to do:**

- Keep import-linter in `pyproject.toml` but only enforce core boundaries
- Remove contracts about policies, event handlers, and other removed layers

**Target contracts:**

```toml
[[tool.importlinter.contracts]]
name = "Routes must not import repositories directly"
type = "forbidden"
source_modules = ["app.routes"]
forbidden_modules = ["app.repositories"]
allow_indirect_imports = true

[[tool.importlinter.contracts]]
name = "Routes must not import database session layer directly"
type = "forbidden"
source_modules = ["app.routes"]
forbidden_modules = ["app.db.session"]
allow_indirect_imports = true

[[tool.importlinter.contracts]]
name = "Services must not import routes"
type = "forbidden"
source_modules = ["app.services"]
forbidden_modules = ["app.routes"]
allow_indirect_imports = true

[[tool.importlinter.contracts]]
name = "Models must not import services"
type = "forbidden"
source_modules = ["app.models"]
forbidden_modules = ["app.services"]
allow_indirect_imports = true
```

### Task 10: Update Exception Handlers

**What to do:**

- Keep only essential exception handlers in `main.py`
- Remove `_error_page_db_session()` context manager
- For custom exceptions that need DB access, use `Depends(get_db)` if needed
- Simplify error pages to not manage sessions manually

**Target approach:**

```python
@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, exc: LoginRequired):
    return RedirectResponse(url="/auth/login", status_code=303)

@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, exc: AuthorizationError):
    # Simple error response, no DB needed for 403
    return JSONResponse(status_code=403, content={"detail": "Forbidden"})
```

## Files to Delete

- `app/events/` (entire directory)
- All event signal definitions
- All event payload classes

## Files to Modify (in priority order)

1. `app/main.py` — simplify bootstrap and lifespan
2. `app/db.py` — remove context variable management
3. `app/core/dependencies.py` — create or update `get_db()` dependency
4. All route files in `app/routes/` — add `db: Session = Depends(get_db)` to handlers
5. All service files in `app/services/` — accept db as parameter, remove event dispatch
6. All repository files in `app/repositories/` — accept db as parameter
7. `app/cli/__init__.py` — simplify session management
8. `pyproject.toml` — simplify import-linter contracts

## Expected Outcomes

- `main.py` should be ~30 lines
- No custom session context management code
- All DB access flows through `Depends(get_db)`
- Services call other services directly, no event system
- Clear linear flow: route → service → repository → model
- No circular dependencies or hidden implicit state
- Import-linting validates clean module boundaries
- App is simpler to understand and test
- All existing functionality preserved

## Testing Approach

- After refactoring, all existing tests should still pass
- Pytest fixtures that use `get_current_session()` should be updated to create sessions normally
- Integration tests should inject `db` session like route handlers do
- Example test pattern:

```python
def test_get_user(db: Session):
    # db is injected by pytest fixture
    user = UserService(db).get_user(1)
    assert user is not None
```

## Preservation of Functionality

- The app should work exactly as it does now, just with cleaner internals
- All migrations, models, and business logic remain unchanged
- User-facing features are untouched
- All existing integrations (payments, email, scheduling) continue to work
