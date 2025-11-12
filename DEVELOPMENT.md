# Local Development Guide

This guide covers local development using Docker and uv package management.

## Prerequisites

- Docker Desktop installed and running
- Git

That's it! Everything else runs in containers.

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo>
cd SouthEast
```

### 2. Start Development Environment

```bash
./dev.sh up
```

This will:
- Build the development Docker images
- Start MySQL database
- Start Django development server (http://localhost:8000)
- Start Tailwind CSS watcher for live CSS compilation

### 3. Run Migrations

```bash
./dev.sh migrate
```

### 4. Create Superuser

```bash
./dev.sh createsuperuser
```

### 5. Access the Application

Open your browser and navigate to: http://localhost:8000

## Development Helper Script

The `./dev.sh` script provides convenient commands for common tasks:

### Basic Commands

```bash
./dev.sh up              # Start development environment
./dev.sh down            # Stop development environment
./dev.sh restart         # Restart services
./dev.sh logs            # Show logs (add service name: logs web)
./dev.sh status          # Show container status
```

### Django Management

```bash
./dev.sh manage <command>        # Run any Django management command
./dev.sh migrate                 # Run migrations
./dev.sh makemigrations          # Create new migrations
./dev.sh createsuperuser         # Create Django superuser
./dev.sh shell                   # Open Python shell in container
./dev.sh dbshell                 # Open MySQL shell
./dev.sh test                    # Run tests
```

### Package Management with uv

```bash
./dev.sh install <package>       # Install new package with uv
./dev.sh install requests        # Example: install requests
./dev.sh install --dev pytest    # Install dev dependency
```

The script will:
1. Install the package using uv inside the container
2. Rebuild the container with new dependencies
3. Restart the service

### Tailwind CSS

```bash
./dev.sh tailwind build          # Build Tailwind CSS once
./dev.sh tailwind start          # Start Tailwind watcher (runs automatically)
```

Note: The Tailwind watcher runs automatically in a separate container when you run `./dev.sh up`.

### Container Management

```bash
./dev.sh build                   # Rebuild Docker images
./dev.sh clean                   # Remove all containers, volumes, and images
```

## Architecture

### Development Setup

The development environment consists of three services:

1. **db** - MySQL 8.0 database
   - Port: 3307 (to avoid conflicts with local MySQL)
   - Data persisted in Docker volume

2. **web** - Django development server
   - Port: 8000
   - Live code reload enabled via volume mounts
   - Runs `python manage.py runserver`

3. **tailwind** - Tailwind CSS watcher
   - Watches for template/CSS changes
   - Automatically recompiles CSS
   - No port needed (background process)

### File Structure

```
.
├── Dockerfile              # Production Dockerfile (Python 3.14)
├── Dockerfile.dev          # Development Dockerfile (Python 3.14)
├── docker-compose.yml      # Development configuration
├── dev.sh                  # Development helper script
├── pyproject.toml          # uv package configuration
└── uv.lock                 # uv lock file
```

## Live Reloading

### Python Code
- All Python code changes are automatically detected
- Django dev server reloads automatically
- No need to rebuild containers

### Templates
- Template changes are immediately reflected
- Tailwind CSS recompiles automatically

### Static Files
- Static files in `static/` directory are served directly
- Changes are immediately visible

### Dependencies
- When adding new packages with `./dev.sh install`, the container rebuilds automatically

## Database

### Connecting to the Database

The MySQL database is accessible at:
- **Host**: localhost
- **Port**: 3307
- **Database**: southeast_archers
- **User**: root
- **Password**: devpassword (default, can be changed in .env)

### Using Database Tools

You can connect with any MySQL client:

```bash
# Via dev.sh script
./dev.sh dbshell

# Or directly with mysql client
mysql -h 127.0.0.1 -P 3307 -u root -pdevpassword southeast_archers
```

### Database Persistence

Database data is stored in a Docker volume named `southeast_mysql_dev_data`. It persists between container restarts.

To reset the database:
```bash
./dev.sh down
docker volume rm southeast_mysql_dev_data
./dev.sh up
./dev.sh migrate
```

## Environment Variables

Development environment variables can be set in `.env` file:

```bash
# .env (for development)
DEBUG=True
SECRET_KEY=dev-secret-key-change-me
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DB_NAME=southeast_archers
DB_USER=root
MYSQL_ROOT_PASSWORD=devpassword

# Ports (optional)
WEB_PORT=8000
DB_PORT_HOST=3307
```

## Working with uv

### Why uv?

uv is a fast Python package manager that's:
- 10-100x faster than pip
- Compatible with pip and requirements.txt
- Built in Rust for maximum performance

### Adding Packages

```bash
# Install a package
./dev.sh install requests

# Install multiple packages
./dev.sh install requests beautifulsoup4

# Install dev dependencies
./dev.sh install --dev pytest pytest-django

# Install specific version
./dev.sh install "django>=5.0,<6.0"
```

### Removing Packages

```bash
./dev.sh manage exec web uv remove <package>
# Then rebuild
./dev.sh build
```

### Updating Packages

```bash
./dev.sh manage exec web uv lock --upgrade-package <package>
./dev.sh build
```

## Common Tasks

### Running Tests

```bash
# Run all tests
./dev.sh test

# Run specific test file
./dev.sh test accounts/tests.py

# Run with coverage
./dev.sh test --cov

# Run with verbose output
./dev.sh test -v
```

### Creating a New App

```bash
./dev.sh manage startapp myapp
```

### Shell Access

```bash
# Django shell
./dev.sh manage shell

# Django shell with iPython
./dev.sh install --dev ipython
./dev.sh manage shell

# Container bash shell
./dev.sh shell
```

### Viewing Logs

```bash
# All logs
./dev.sh logs

# Specific service
./dev.sh logs web
./dev.sh logs db
./dev.sh logs tailwind

# Follow logs (live updates)
./dev.sh logs -f web
```

### Database Operations

```bash
# Create migrations
./dev.sh makemigrations

# Apply migrations
./dev.sh migrate

# Create specific migration
./dev.sh makemigrations accounts

# Show migrations
./dev.sh manage showmigrations

# Rollback migration
./dev.sh manage migrate accounts 0001

# Reset database
./dev.sh manage flush
```

## Troubleshooting

### Port Already in Use

If port 3307 or 8000 is already in use, change it in `.env`:

```bash
WEB_PORT=8001
DB_PORT_HOST=3308
```

### Container Won't Start

```bash
# Check logs
./dev.sh logs

# Rebuild from scratch
./dev.sh build

# Clean everything and start fresh
./dev.sh clean
./dev.sh up
```

### Database Connection Issues

```bash
# Check database is running
./dev.sh status

# Check database logs
./dev.sh logs db

# Restart database
docker-compose restart db
```

### Tailwind CSS Not Compiling

```bash
# Check Tailwind container logs
./dev.sh logs tailwind

# Restart Tailwind service
docker-compose restart tailwind

# Manually rebuild CSS
./dev.sh tailwind build
```

### Permission Issues

If you encounter permission issues with files:

```bash
# Fix ownership (run on host)
sudo chown -R $USER:$USER .
```

### Node Modules Issues

If Tailwind fails due to node_modules:

```bash
# Remove node_modules volume
docker volume rm southeast_node_modules

# Rebuild and restart
./dev.sh build
./dev.sh up
```

## Performance Tips

### Volume Performance on macOS/Windows

Docker volumes can be slow on macOS and Windows. To improve performance:

1. Ensure Docker Desktop has adequate resources allocated (Settings → Resources)
2. Consider using Docker Desktop's "VirtioFS" file sharing (macOS)
3. Use named volumes for node_modules (already configured)

### Faster Builds

```bash
# Use BuildKit for faster builds (already default in modern Docker)
export DOCKER_BUILDKIT=1

# Build with cache
./dev.sh build  # Uses cache by default

# Build without cache (slower but fresh)
docker-compose build --no-cache
```

## IDE Integration

### VS Code

Install the following extensions:
- Python
- Docker
- Django

Add to `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "/usr/local/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true
  }
}
```

Attach to the running container:
1. Install "Dev Containers" extension
2. Command Palette → "Dev Containers: Attach to Running Container"
3. Select `southeast_web_dev`

### PyCharm

1. Go to Settings → Project → Python Interpreter
2. Add → Docker Compose
3. Select `docker-compose.yml`
4. Choose the `web` service

## Development vs Production

### Development (docker-compose)

```bash
./dev.sh up
# Runs Django dev server with live reload
# Tailwind watcher runs automatically
# DEBUG=True
```

### Production (Dockerfile only)

Production doesn't use docker-compose. See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment instructions.

To test the production Docker build locally:
```bash
docker build -t southeast:test .
docker run -p 8000:8000 -e DEBUG=False -e SECRET_KEY=test southeast:test
```

## Next Steps

- Read [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment guide
- Check [README.md](README.md) for project overview
- Review Django settings in `config/settings.py`

## Getting Help

If you encounter issues:

1. Check the logs: `./dev.sh logs`
2. Verify containers are running: `./dev.sh status`
3. Try rebuilding: `./dev.sh build`
4. Clean slate: `./dev.sh clean && ./dev.sh up`

For Django-specific issues, see: https://docs.djangoproject.com/
For Docker issues, see: https://docs.docker.com/
