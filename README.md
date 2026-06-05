# South East Archers Club Website

A web application for South East Archers club management, including membership management, shoot scheduling, event booking, payment processing, and member communications.

## Features

### Member Features
- Membership management — sign up, view status, and renew annual membership
- Shoot registration — browse and register for scheduled club shoots
- Credits system — track included credits and purchase additional shoot credits
- Payment processing — pay by card (SumUp) or cash with admin approval
- Personal dashboard — view membership status, credits, shoot history, and payments

### Admin Features
- Member management — create, edit, and manage member accounts and memberships
- Shoot management — schedule shoots, track attendance, manage locations
- Event and news management — create and publish club content
- Payment approvals — approve pending cash payments
- Settings — configure membership costs, year dates, and payment instructions
- Role-based access control — fine-grained permissions for admin functions

### Automated Tasks
- Membership expiry on the configured year-start date
- Weekly low-credits email reminders

## Stack

- **Backend:** Python 3.14+, FastAPI, Uvicorn/Gunicorn
- **Database:** MySQL with SQLAlchemy and Alembic migrations
- **Package manager:** [UV](https://github.com/astral-sh/uv)
- **Frontend:** Vite 7, Tailwind CSS 4, Alpine.js
- **Payments:** SumUp API
- **Email:** SMTP (stdlib)
- **Task scheduling:** Custom scheduler (`app/scheduler/`)

## Requirements

- Python 3.14+
- Node.js (LTS)
- MySQL
- [UV](https://docs.astral.sh/uv/getting-started/installation/)

## Installation & Setup

```bash
git clone <repository-url>
cd SouthEastArchers
cp .env.example .env
make install
uv run python -m app.cli db upgrade
uv run python -m app.cli rbac seed
```

Create an admin user via the admin members UI after starting the app, or insert one directly in the database.

## Running the Application

### Development

```bash
make dev
```

- FastAPI: http://localhost:8000
- Vite: http://localhost:5173

### Scheduled Tasks

Run due scheduled jobs (membership expiry, low-credits reminders) via your scheduler entry point or cron calling the relevant functions in `app/scheduler/jobs/`.

## Project Structure

```
├── app/
│   ├── main.py             # FastAPI application (ASGI entry: app.main:app)
│   ├── routes/             # HTTP routes (admin, member, auth, payment, public)
│   ├── services/           # Business logic
│   ├── repositories/       # Data access
│   ├── models/             # SQLAlchemy models
│   ├── db/                 # Database session layer
│   ├── schemas/            # Pydantic models and form schemas
│   ├── resources/          # Templates and frontend assets
│   │   ├── templates/      # Jinja2 templates
│   │   └── static/         # CSS/JS source; dist/ holds Vite build output
│   └── scheduler/          # Scheduled jobs
├── tests/                  # Test suite (feature/, unit/)
└── migrations/             # Alembic migrations
```

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Install Python and Node dependencies |
| `make dev` | Run FastAPI with reload and watch-built assets |
| `make setup` | Install dependencies and build assets |
| `make test` | Run the test suite |
| `make test-coverage` | Run tests with coverage report |
| `make lint` | Run Ruff checks |
| `uv run sea db upgrade` | Apply database migrations |
| `uv run sea rbac seed` | Seed default roles and permissions |
| `uv run sea scheduler list` | List scheduled jobs |
| `uv run sea scheduler run <job>` | Run a scheduled job (for cron) |

### Cron jobs

Run these via system cron (example, daily at 00:01 and weekly Monday 09:00):

```cron
1 0 * * * cd /path/to/SouthEastArchers && uv run sea scheduler run expire-memberships
0 9 * * 1 cd /path/to/SouthEastArchers && uv run sea scheduler run low-credits-reminder
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (`development`, `testing`, `production`) | `development` |
| `SECRET_KEY` | Session signing key | (required in production) |
| `DATABASE_URL` | MySQL connection string | (required) |
| `MAIL_SERVER` | SMTP server | `localhost` |
| `MAIL_PORT` | SMTP port | `587` |
| `SUMUP_API_KEY` | SumUp API key | (required for card payments) |
| `SUMUP_MERCHANT_CODE` | SumUp merchant code | (required for card payments) |

`FLASK_ENV` is still accepted as an alias for `APP_ENV` for backward compatibility.

## Docker

```bash
docker build -t southeastarchers .
docker run -p 5000:5000 --env-file .env southeastarchers
```

The container waits for the database, runs migrations via `app.cli`, seeds RBAC, and serves the app with Gunicorn + Uvicorn workers on port 5000.

## License

TODO: Add license information.
