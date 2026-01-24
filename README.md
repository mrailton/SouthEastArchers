# South East Archers Club Website

A Flask-based membership management system for South East Archers archery club.

## Features

- **Member Management**: User registration, authentication, and membership tracking
- **Payment Processing**: Online payments via SumUp integration
- **Events & Shoots**: Schedule and manage club events and shooting sessions
- **News**: Publish club news and announcements
- **Admin Dashboard**: Comprehensive admin tools for managing members, events, and finances

## Technology Stack

- **Backend**: Flask 3.1 with SQLAlchemy ORM
- **Database**: MySQL/MariaDB (SQLite for testing)
- **Frontend**: Alpine.js + Tailwind CSS (built with Vite)
- **Email**: Flask-Mail with SMTP
- **Payments**: SumUp API integration
- **Task Scheduling**: Laravel-style cron scheduler
- **Deployment**: Docker with Gunicorn

## Local Development

### Prerequisites

- Python 3.14+
- Node.js LTS
- MySQL/MariaDB (or use SQLite for development)
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SouthEastArchers
   ```

2. **Install dependencies**
   ```bash
   make install
   ```
   This installs both Python and Node.js dependencies.

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

4. **Initialize database**
   ```bash
   make db-upgrade
   ```

5. **Run development server**
   ```bash
   make dev
   ```
   This starts:
   - Flask dev server on http://localhost:5000
   - Vite dev server for hot-reloading assets

### Available Commands

All commands are available via `manage.py`:

```bash
# Show all available commands
python manage.py --help

# Development
python manage.py install      # Install all dependencies
python manage.py dev          # Run Flask + Vite dev servers
python manage.py shell        # Interactive Python shell

# Testing
python manage.py test run     # Run all tests
python manage.py test run -c  # Run with coverage
python manage.py test run -v  # Verbose output

# Code Quality
python manage.py lint format          # Format code with black/isort
python manage.py lint format --check  # Check formatting only
python manage.py lint check           # Run flake8
python manage.py lint typecheck       # Run mypy

# Database
python manage.py db upgrade           # Apply migrations
python manage.py db migrate -m "msg"  # Create migration

# Assets
python manage.py assets build   # Build production assets
python manage.py assets watch   # Watch for changes

# Task Scheduling
python manage.py schedule list   # List scheduled tasks
python manage.py schedule run    # Run tasks that are due

# Utilities
python manage.py clean          # Remove cache files
python manage.py stats          # Show app statistics
```

## Project Structure

```
SouthEastArchers/
├── app/
│   ├── __init__.py         # App factory
│   ├── config.py           # Configuration
│   ├── models/             # Database models
│   ├── routes/             # View controllers
│   ├── services/           # Business logic
│   ├── forms/              # WTForms
│   ├── templates/          # Jinja2 templates
│   ├── utils/              # Helper functions
│   ├── scheduler/          # Task scheduler module
│   │   ├── __init__.py     #   - Public API
│   │   ├── event.py        #   - Event class
│   │   ├── schedule.py     #   - Schedule class
│   │   └── jobs/           #   - Scheduled job functions
│   │       ├── __init__.py
│   │       └── *.py
│   └── schedule.py         # Scheduled task definitions
├── resources/
│   ├── css/                # Tailwind CSS source
│   ├── js/                 # Alpine.js components
│   └── static/             # Built assets (generated)
├── tests/                  # Test suite
├── migrations/             # Database migrations
├── docs/                   # Documentation
│   └── SCHEDULING.md       # Task scheduler guide
├── web.py                  # WSGI entry point
├── manage.py               # CLI management commands
├── Dockerfile              # Production container
├── docker-entrypoint.sh    # Container startup script
├── pyproject.toml          # Python dependencies
├── package.json            # Node.js dependencies
└── vite.config.js          # Vite build config
```

## Configuration

Key environment variables (see `.env.example`):

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Flask secret key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
- `MAIL_*`: SMTP server configuration
  - **Local Development**: Use mailhog/mailcatcher on port 1025 (no auth needed)
  - **Production**: Configure real SMTP server with credentials
- `SUMUP_API_KEY`: SumUp payment API key
- `SUMUP_MERCHANT_CODE`: SumUp merchant identifier

### Email Setup for Development

For local development, use a mail catcher like [MailHog](https://github.com/mailhog/MailHog):

```bash
# Install mailhog (macOS)
brew install mailhog

# Run mailhog
mailhog

# View emails at http://localhost:8025
```

Then configure in `.env`:
```bash
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USE_TLS=False
# Leave MAIL_USERNAME and MAIL_PASSWORD commented out
```

## Testing

### Task Scheduling

The app includes a Laravel-style task scheduler. See [docs/SCHEDULING.md](docs/SCHEDULING.md) for full documentation.

Quick example:
```python
# In app/schedule.py
from app.scheduler import schedule

def cleanup_task():
    print("Cleaning up!")

schedule.call(cleanup_task, "Daily cleanup").daily_at("02:00")
```

Set up cron job:
```bash
* * * * * cd /path/to/project && /path/to/python manage.py schedule run >> /dev/null 2>&1
```

## Testing

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test file
uv run pytest tests/models/test_user.py

# Run with verbose output
uv run pytest -v
```

## Deployment

### Docker

Build and run with Docker:

```bash
# Build image
docker build -t southeastarchers .

# Run container
docker run -p 5000:5000 \
  -e DATABASE_URL=mysql+pymysql://user:pass@host/db \
  -e SECRET_KEY=your-secret-key \
  -e SUMUP_API_KEY=your-api-key \
  southeastarchers
```

### Production Checklist

1. Set strong `SECRET_KEY`
2. Configure production database
3. Set up SMTP for email delivery
4. Configure SumUp API credentials
5. Set `FLASK_ENV=production`
6. Use HTTPS (set `PREFERRED_URL_SCHEME=https`)
7. Configure proper `SERVER_NAME` for your domain

## Architecture

This is a straightforward Flask application following best practices:

- **Application Factory Pattern**: `create_app()` in `app/__init__.py`
- **Blueprints**: Organized routes (public, auth, member, admin, payment)
- **Service Layer**: Business logic separated from routes
- **ORM Models**: SQLAlchemy for database abstraction
- **Form Validation**: Flask-WTF with WTForms
- **Email**: Synchronous email sending via Flask-Mail
- **Asset Pipeline**: Vite for modern frontend tooling

### Email Handling

Emails are sent synchronously using Flask-Mail. For a club website with moderate traffic, this is simpler and more reliable than background job queues.

### Payment Flow

1. User initiates payment (membership/credits)
2. Create checkout session with SumUp
3. Process payment with card details
4. Update database records
5. Send receipt email
6. Redirect to success page

## License

[Add license information]

## Support

[Add contact/support information]
