# Architecture

South East Archers is a server-rendered FastAPI application for club management: memberships, shoots, payments, and finance.

## Layer overview

```
HTTP request
    → routes/          (parse forms, call services, render templates)
    → services/        (business logic, ServiceResult)
    → repositories/    (SQLAlchemy queries)
    → models/          (ORM entities)
```

Side effects (email, ledger entries) go through **events** (`app/events/`) and run after the HTTP response is sent.

| Layer | May import | Must not import |
|-------|------------|-----------------|
| `routes/` | `services`, `schemas`, `dependencies` | `repositories`, `db`, `policies`, `events` |
| `services/` | `repositories`, `events` | `db.session` directly |
| `repositories/` | `db`, `models` | `routes`, `services` |
| `events/handlers/` | `services` | `repositories` |
| `schemas/` | Pydantic, enums | `services`, `routes` |

Boundaries are enforced by [import-linter contracts](pyproject.toml).

## Database session rules

SQLAlchemy uses a **sync** session stored in a `ContextVar` (`app/db/session.py`).

| Context | Session lifecycle |
|---------|-------------------|
| HTTP requests | `Depends(get_db)` on `api_router` opens a session per request |
| Deferred event handlers | `run_handler_with_session()` opens a fresh session after the response |
| CLI / scheduler | `app/cli` opens and closes its own session |
| Tests | `conftest.py` uses transaction rollback per test |

Repositories call `db.session` implicitly. When adding code outside HTTP requests, ensure a session is active or use `BaseRepository.transaction()`.

### Commit convention

`get_db` opens a session per request but **does not auto-commit** on success. Uncommitted work is discarded when the session closes.

| Pattern | When to use |
|---------|-------------|
| `with BaseRepository.transaction():` | Multi-step writes that must commit or roll back together |
| `SomeRepository.save()` | Single logical unit after `add()` / in-place mutations |
| `SomeRepository.flush()` | Need generated IDs before an external API call, then `save()` |

New code should use one of these explicitly. Do not rely on the request ending to persist changes.

`Model.query` is deprecated (Flask-style legacy). Use repositories or `session.scalars(select(...))` in `app/` code.

## ServiceResult

Services return `ServiceResult[T]` (`app/services/result.py`):

- `success` / `message` / optional `data` / `error_code` / `warnings`
- Routes check `result.success` and flash messages; some admin routes map `ErrorCode.NOT_FOUND` to HTTP 404

## Payment flow

```mermaid
sequenceDiagram
    participant Member
    participant Route
    participant Service
    participant SumUp
    participant Event
    participant Mail
    participant Finance

    Member->>Route: POST /payment/membership
    Route->>Service: initiate_membership_payment()
    Service->>SumUp: create_checkout()
    Service-->>Route: checkout_id + payment_id (pending)
    Route->>Member: redirect to SumUp widget

    Member->>Route: POST /payment/checkout/{id}/complete
    Route->>Service: fulfill_checkout()
    Service->>SumUp: get_checkout() — must be PAID
    Service->>Service: fulfill_payment() — mark complete, apply credits/membership
    Service->>Event: payment_completed / credit_purchased
    Route->>Member: redirect + flash

    Note over Event,Finance: After HTTP response
    Event->>Mail: send receipt
    Event->>Finance: record_payment_transactions (idempotent)
```

### Failed / abandoned checkouts

If SumUp returns `FAILED` or `CANCELLED` on `/payment/checkout/{id}/complete`, `fulfill_checkout` marks the `Payment` as `failed` in the DB and redirects to the member dashboard with a flash message.

Members can **retry** a failed or pending online payment from their dashboard without creating a new `Payment` record:

1. `POST /payment/{payment_id}/retry` → `payments.retry_payment()`
2. If the original SumUp checkout is still `PENDING`, it is reused; otherwise a new SumUp checkout is created and the existing `Payment` record is updated with the new `sumup_checkout_id` and reset to `pending`.
3. The member is redirected to the SumUp widget as normal.

Admins can **cancel** any pending or failed payment from the member detail page:

- `POST /admin/payments/{payment_id}/cancel` → `payments.cancel_payment()` — works for both cash and online payments.

### Cash payments

1. Member submits cash request → `initiate_cash_*` creates pending payment, commits, then emits `cash_payment_submitted` (pending email).
2. Admin approves → `approve_cash_payment` → `fulfill_payment` → `payment_completed` → mail + ledger.
3. Admin can also reject or cancel pending cash payments from the member detail page.

### Admin reconciliation (SumUp)

There is no SumUp webhook. Completion depends on the member POSTing `/payment/checkout/{id}/complete` after SumUp reports PAID. If the browser session is lost, pending online payments with a stored `sumup_checkout_id` appear on **Admin → Reconcile Online Payments**, where an admin verifies status with SumUp and fulfills manually.

Payment fulfillment handlers verify `payment.user_id` matches the acting user before applying effects.

### Handler replay (recovery)

If a completed payment is missing its receipt or ledger entry after a deferred handler failure, replay side effects:

- **CLI:** `uv run sea payments replay-side-effects PAYMENT_ID` (`--no-mail` for ledger only)
- **Admin:** Reconcile page → "Replay side effects" form

Ledger recording is idempotent on replay.

### Idempotency

- Ledger: `receipt_reference` + category + type (DB unique constraint)
- SumUp txn: `external_transaction_id` unique on `payments`
- Cash: `cash-payment-{payment_id}` receipt reference
- Fulfillment: `fulfill_payment()` no-ops when status is already `completed`

## Events

Signals live in `app/events/__init__.py`. **Emit through typed helpers** in `app/events/payloads.py` (do not call `.send()` with raw kwargs from services). Handlers in `app/events/handlers.py` parse payloads and call `mail` and `finance` services only.

**Emit events only after a successful commit** (see `users.create_user` and cash payment initiation).

In production, handlers are deferred to a background thread after the response. In tests (`APP_ENV=testing`), they run synchronously in middleware.

### Receipt and ledger paths

| Path | Mail | Ledger | When |
|------|------|--------|------|
| `emit_payment_side_effects` → `payment_completed` / `credit_purchased` | via handler | via handler | Normal checkout, cash approval, admin reconcile |
| `membership_activated` event | via handler | no | Admin activates membership when a completed payment exists but `payment_completed` was not emitted |
| `replay_payment_side_effects` | direct `mail` service | direct `finance` service | Recovery after handler failure (idempotent ledger) |

Use `emit_payment_side_effects` for all new fulfillment flows. Use replay only for operations recovery.

### Handler failures

Deferred handlers log failures with `user_id` / `payment_id` context; they do not retry automatically. For payments, use **Handler replay** above. For other events, check application logs for `Deferred event handler failed`.

## Adding a feature (checklist)

1. **Model** in `app/models/` if the feature needs new DB tables — follow existing `mapped_column` / `relationship` patterns.
2. **Migration** — `alembic revision --autogenerate -m "description"` and review the generated file before applying.
3. **Schema** in `app/schemas/` if the route accepts form input.
4. **Service** method returning `ServiceResult` — business logic lives here, not in routes.
5. **Repository** method if the query is non-trivial — keep raw `db.session` calls out of services.
6. **Route** with `CsrfFormData` on POST and `require_perms()` on admin routes.
7. **Templates** in `app/resources/templates/` — extend `base.html` or `admin/base.html`; use existing Tailwind utility classes.
8. **`app/routes_map.py`** — add any new named routes that need to be resolved outside of HTTP request context (emails, CLI, scheduler).
9. **Unit test** for service logic; **feature test** for HTTP happy path.
10. **Event + handler** only if the action sends email or writes to the ledger — see `app/events/`.

## Beginner courses (planned feature notes)

The planned beginner courses feature will need:

- **New models:** `Course`, `CourseSession` (many sessions per course), `CourseEnrollment` (with status: enrolled/waitlisted/cancelled/completed). Keep these separate from `Event` — events are single-date announcements, not multi-session operational entities.
- **Non-member enrollment:** `Payment.user_id` is currently non-nullable, so course fees require either creating a lightweight account before enrollment/payment or a separate `CoursePayment` model. The simplest approach is to require account creation as step 1 of enrollment.
- **Reuse:** RBAC/permissions pattern, email/event infrastructure, payment reconciliation/replay, the `qualification` field on memberships for marking course completion, and `ShootVisitor` as prior art for non-member participation.
- **New signals:** `course_enrollment_confirmed`, `course_reminder_due`, `course_completed`.
- **Scheduler jobs:** enrollment reminder emails, waitlist promotion on cancellation.

## Testing

| Suite | Location | Database |
|-------|----------|----------|
| Unit | `tests/unit/` | SQLite in-memory (`create_all`) |
| Feature | `tests/feature/` | SQLite in-memory |
| Integration | `tests/integration/` | MySQL via `TEST_DATABASE_URL` (CI) |

CI runs `alembic upgrade head` before tests so production schema parity is validated.

## Configuration

See `.env.example`. Production requires `SECRET_KEY`, MySQL `DATABASE_URL`, `MAIL_SERVER`, and `REDIS_URL` (multi-worker rate limiting).
