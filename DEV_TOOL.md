# Development Tool Guide

The `dev.sh` script is a comprehensive shell-based CLI tool for managing development tasks locally. It wraps Docker commands and application-specific operations, requiring only bash (no Python dependencies needed).

## Installation

The tool requires:
- Bash shell
- Docker and Docker Compose
- Standard Unix utilities (find, grep, etc.)

## Quick Start

```bash
# Make the script executable (if needed)
chmod +x dev.sh

# Show all available commands
./dev.sh help

# Quick start (start services + init DB)
./dev.sh start

# Stop services
./dev.sh stop

# View status
./dev.sh status
```

## Command Categories

### 🚀 Quick Commands

#### `start`
Quick start the entire development environment
```bash
./dev.sh start
```
This:
1. Starts all Docker services
2. Initializes the database
3. Shows status and URLs

#### `stop`
Stop all services
```bash
./dev.sh stop
```

#### `info`
Show project information and tech stack
```bash
./dev.sh info
```

---

### 🐳 Docker Management

#### `up`
Start all Docker services
```bash
./dev.sh up
```

#### `down`
Stop all Docker services
```bash
./dev.sh down
```

#### `restart`
Restart all services
```bash
./dev.sh restart
```

#### `logs`
View service logs
```bash
# View app logs (default)
./dev.sh logs

# Follow logs in real-time
./dev.sh logs -f

# View specific service
./dev.sh logs -s sea_mysql

# Follow MySQL logs
./dev.sh logs -f -s sea_mysql
```

#### `ps`
Show running services
```bash
./dev.sh ps
```

#### `shell`
Open interactive bash shell in app container
```bash
./dev.sh shell
```

#### `build`
Rebuild Docker image
```bash
./dev.sh build
```

---

### 🗄️ Database Management

#### `db:init`
Initialize database with schema
```bash
./dev.sh db:init
```

#### `db:migrate`
Create a new database migration
```bash
./dev.sh db:migrate "Add user email uniqueness"
```

#### `db:upgrade`
Apply pending migrations
```bash
./dev.sh db:upgrade
```

#### `db:downgrade`
Rollback the last migration (with confirmation)
```bash
./dev.sh db:downgrade
```

#### `db:reset`
⚠️ Reset database (dangerous - deletes all data, requires confirmation)
```bash
./dev.sh db:reset
```

---

### 👤 User Management

#### `user:create`
Create a new user
```bash
# Create regular member
./dev.sh user:create

# Create admin user
./dev.sh user:create --admin
```

#### `user:list`
List all users
```bash
./dev.sh user:list
```

#### `user:delete`
Delete a user (with confirmation)
```bash
./dev.sh user:delete
```

---

### 🧪 Testing & Quality

#### `test`
Run the test suite
```bash
# Basic test run
./dev.sh test

# With verbose output
./dev.sh test -v
```

#### `test:file`
Run tests for a specific file
```bash
./dev.sh test:file tests/unit/test_models.py
```

#### `test:coverage`
Generate coverage report (HTML)
```bash
./dev.sh test:coverage

# Open: htmlcov/index.html
```

#### `lint`
Run code linting (flake8)
```bash
./dev.sh lint
```

#### `format`
Format code with black and isort
```bash
./dev.sh format
```

---

### 🛠️ Development Utilities

#### `status`
Show development environment status
```bash
./dev.sh status
```

Shows:
- Docker services status (ps output)
- Database connection status
- Available service URLs

#### `stats`
Show application statistics
```bash
./dev.sh stats
```

Shows:
- Total users and memberships
- Active memberships
- Upcoming shooting nights

#### `clean`
Clean up cache and temp files
```bash
./dev.sh clean
```

Cleans:
- Python `__pycache__` directories
- `.pyc` files
- pytest cache (.pytest_cache)

---

## Common Workflows

### Starting Development

```bash
# 1. Start everything
./dev.sh start

# 2. Create admin user
./dev.sh user:create --admin

# 3. Check status
./dev.sh status

# 4. View app
# Open http://localhost:5000
```

### Making Database Changes

```bash
# 1. Modify a model in app/models/

# 2. Create migration
./dev.sh db:migrate "Description of change"

# 3. Apply migration
./dev.sh db:upgrade

# 4. Run tests
./dev.sh test
```

### Testing Code Changes

```bash
# 1. Format code
./dev.sh format

# 2. Lint code
./dev.sh lint

# 3. Run tests
./dev.sh test

# 4. Check coverage
./dev.sh test:coverage
# Open htmlcov/index.html
```

### Debugging Issues

```bash
# 1. View logs (follow in real-time)
./dev.sh logs -f

# 2. Check database/container shell
./dev.sh shell

# 3. Run specific test
./dev.sh test:file tests/unit/test_models.py

# 4. Check status
./dev.sh status
```

### Production-Like Testing

```bash
# 1. Rebuild Docker image
./dev.sh build

# 2. Restart services
./dev.sh restart

# 3. Run full test suite
./dev.sh test

# 4. Check coverage
./dev.sh test:coverage
```

---

## Environment Access

The tool provides easy access to development services:

| Service | URL | Credentials |
|---------|-----|-------------|
| Flask App | http://localhost:5000 | - |
| MailHog | http://localhost:8025 | - |
| MySQL | localhost:3306 | user: `sea_user`, pass: `sea_password` |

---

## Aliases for Quick Access

Add these aliases to your shell profile (`.bashrc`, `.zshrc`, etc.) for faster access:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias dev='./dev.sh'
alias dev-start='./dev.sh start'
alias dev-stop='./dev.sh stop'
alias dev-logs='./dev.sh logs -f'
alias dev-test='./dev.sh test'
alias dev-shell='./dev.sh shell'
alias dev-status='./dev.sh status'
```

Then use:
```bash
dev start
dev stop
dev-logs
dev-test
dev-shell
dev-status
```

---

## Troubleshooting

### "Docker command not found"
- Ensure Docker is installed: `docker --version`
- Ensure Docker Compose is installed: `docker-compose --version`

### "dev.sh: command not found"
Make the script executable:
```bash
chmod +x dev.sh
```

### "Services not running"
```bash
./dev.sh up
./dev.sh db:init
```

### "Cannot connect to database"
```bash
# Check database status
./dev.sh status

# Restart database service
./dev.sh restart
```

### "Tests failing after model changes"
```bash
# Ensure migrations are applied
./dev.sh db:upgrade

# Run tests
./dev.sh test
```

### "Need to reset everything"
```bash
# Stop services and remove volumes
./dev.sh down
docker-compose down -v

# Start fresh
./dev.sh start
./dev.sh user:create --admin
```

---

## Tips & Tricks

### Continuous Testing
```bash
# Watch tests (requires 'watch' command)
watch './dev.sh test'
```

### Database Inspection
```bash
# Open database shell
docker-compose exec sea_mysql mysql -u sea_user -psea_password sea_db

# List tables
SHOW TABLES;

# View users
SELECT * FROM users;
```

### Code Quality
```bash
# Format all code
./dev.sh format

# Run full quality check
./dev.sh format && ./dev.sh lint && ./dev.sh test
```

### Quick Debugging
```bash
# View real-time logs
./dev.sh logs -f

# In another terminal, trigger the action:
# - Visit http://localhost:5000
# - Or use: ./dev.sh user:create
```

### View All Available Commands
```bash
# Show help and all commands
./dev.sh help
```

---

## Requirements

The `dev.sh` script requires only standard tools that should be available on any Unix/Linux system with Docker installed:

- **bash** - Shell interpreter
- **docker** - Container runtime
- **docker-compose** - Container orchestration
- **Standard Unix utilities**: find, grep, sed, awk

No Python dependencies needed for the dev tool itself (only for the Flask application, which is handled in the Docker container).

---

## Notes

- All commands use Docker Compose, so services must be running for most operations
- Database operations require the app container to be running
- Destructive operations (like `db:reset`) require confirmation for safety
- The script is portable - works on macOS, Linux, and Windows (WSL2)
- Make sure the script is executable: `chmod +x dev.sh`
- Color-coded output for better readability:
  - 🔵 Blue (`📍`) = Information
  - 🟢 Green (`✅`) = Success
  - 🔴 Red (`❌`) = Errors
  - 🟡 Yellow (`⚠️`) = Warnings

