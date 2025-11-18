# Management Script Guide

The `manage.py` script is the central management tool for the South East Archers application.

## Usage

All commands use UV to run in the correct environment:

```bash
uv run python manage.py <command> [options]
```

## Available Commands

### Server Commands

**Run development server:**
```bash
uv run python manage.py runserver
uv run python manage.py runserver --port 8000 --no-debug
```

**Open Python shell with app context:**
```bash
uv run python manage.py shell
```

### Database Commands

**Initialize migrations (first time only):**
```bash
uv run python manage.py db init
```

**Create a migration:**
```bash
uv run python manage.py db migrate -m "Add user table"
```

**Apply migrations:**
```bash
uv run python manage.py db upgrade
```

**Rollback last migration:**
```bash
uv run python manage.py db downgrade
```

**Reset database (WARNING: deletes all data):**
```bash
uv run python manage.py db reset
```

### User Management

**Create a regular user:**
```bash
uv run python manage.py user create
```

**Create an admin user with membership (recommended):**
```bash
uv run python manage.py user admin
```

**Create user with options:**
```bash
uv run python manage.py user create --admin --with-membership
```

**List all users:**
```bash
uv run python manage.py user list
```

**Delete a user:**
```bash
uv run python manage.py user delete --id 1
```

### Testing

**Run all tests:**
```bash
uv run python manage.py test run
```

**Run tests with coverage:**
```bash
uv run python manage.py test run -c
```

**Run tests with verbose output:**
```bash
uv run python manage.py test run -v
```

**Run specific test file:**
```bash
uv run python manage.py test file tests/test_models.py
```

**Run tests matching keyword:**
```bash
uv run python manage.py test run -k user
```

**Generate coverage report:**
```bash
uv run python manage.py test coverage
```

### Code Quality

**Check code with flake8:**
```bash
uv run python manage.py lint check
```

**Format code with black and isort:**
```bash
uv run python manage.py lint format
```

**Check formatting without changing files:**
```bash
uv run python manage.py lint format --check
```

### Shoot Management

**Create a shoot:**
```bash
uv run python manage.py shoot create
```

**List all shoots:**
```bash
uv run python manage.py shoot list
```

**List upcoming shoots only:**
```bash
uv run python manage.py shoot list --upcoming
```

### Statistics

**Show application statistics:**
```bash
uv run python manage.py stats
```

### Utilities

**Install dependencies:**
```bash
uv run python manage.py install
```

**Clean cache and temp files:**
```bash
uv run python manage.py clean
```

## Quick Start Guide

1. **Install dependencies:**
   ```bash
   uv sync --group dev
   ```

2. **Apply database migrations:**
   ```bash
   uv run python manage.py db upgrade
   ```

3. **Create an admin user:**
   ```bash
   uv run python manage.py user admin
   ```

4. **Run the development server:**
   ```bash
   uv run python manage.py runserver
   ```

5. **Run tests:**
   ```bash
   uv run python manage.py test run
   ```

## Shortcuts

You can also make manage.py executable and run directly with UV:

```bash
chmod +x manage.py
uv run ./manage.py runserver
uv run ./manage.py user admin
uv run ./manage.py test run
```

Or create an alias in your shell config:

```bash
alias manage="uv run python manage.py"
```

Then use:
```bash
manage runserver
manage user admin
manage test run
```
