# Docker Setup Guide

This directory contains all Docker-related files for the South East Archers application.

## Files Overview

- **docker-compose.yml** - Production configuration using pre-built GHCR images
- **docker-compose.build.yml** - Production configuration that builds images locally
- **docker-compose.dev.yml** - Development configuration with hot-reload
- **Dockerfile.web** - Multi-stage build for web application
- **Dockerfile.worker** - Background worker for RQ jobs
- **Dockerfile.dev** - Development image with all dev tools
- **docker-entrypoint.sh** - Entrypoint script that runs migrations

## Quick Start

### Development (Recommended)

Start the entire development stack with one command:

```bash
make docker-up
```

This starts:
- **MySQL 8.4** database (port 3306)
- **Redis 7** for background jobs (port 6379)
- **Web** application with hot-reload (port 5000)
- **Worker** with auto-restart on code changes
- **Mailhog** for email testing (port 8025)

Access the application at http://localhost:5000

View logs:
```bash
make docker-logs
```

Stop all services:
```bash
make docker-down
```

### Development Features

- **Hot Reload**: Code changes are automatically detected
- **Auto-restart**: Worker restarts when Python files change
- **Email Testing**: All emails visible in Mailhog at http://localhost:8025
- **Volume Mounts**: Your local code is mounted in containers
- **No local dependencies**: No need to install Python, Node, MySQL, or Redis locally

### Useful Commands

```bash
# Rebuild containers after dependency changes
make docker-rebuild

# Open shell in web container
make docker-shell

# Open MySQL shell
make docker-db-shell

# View logs
make docker-logs
```

## Production Deployment (Dokploy)

### Recommended: Using Pre-built GHCR Images

The default `docker-compose.yml` uses pre-built images from GitHub Container Registry (GHCR). This is the recommended approach for Dokploy.

**Images:**
- `ghcr.io/mrailton/southeastarchers-web:latest`
- `ghcr.io/mrailton/southeastarchers-worker:latest`

**How it works:**
1. GitHub Actions automatically builds and pushes images on every push to `main`
2. Dokploy pulls the latest images from GHCR
3. No build step needed on the server (faster deployments)

**Setup in Dokploy:**

1. Push your code to a Git repository
2. In Dokploy, create a new "Compose" application
3. Point it to your repository
4. Set the compose file path to `docker/docker-compose.yml`
5. Add environment variables in Dokploy UI
6. Deploy!

Dokploy will automatically:
- Pull latest images from GHCR
- Start MySQL and Redis
- Run database migrations automatically
- Expose the web service

### Alternative: Build Images Locally

If you prefer to build images on the Dokploy server instead of pulling from GHCR:

1. Use `docker/docker-compose.build.yml` instead
2. Set compose file path to `docker/docker-compose.build.yml` in Dokploy
3. Dokploy will build images during deployment

**Trade-offs:**
- **GHCR (default)**: Faster deployments, pre-tested images, consistent builds
- **Local build**: No external registry needed, build on-demand

### Manual Deployment

To pull and run the production images manually:

```bash
# Pull latest images and start services
cd docker
docker-compose pull
docker-compose up -d

# Or build images locally
docker-compose -f docker-compose.build.yml up -d --build
```

### GitHub Actions Integration

Images are automatically built and pushed to GHCR on every push to `main` via GitHub Actions.

**Workflow:** `.github/workflows/ci.yml`

**What happens:**
1. Tests run on every push
2. On `main` branch push:
   - Builds `docker/Dockerfile.web` → `ghcr.io/mrailton/southeastarchers-web:latest`
   - Builds `docker/Dockerfile.worker` → `ghcr.io/mrailton/southeastarchers-worker:latest`
   - Pushes to GitHub Container Registry
   - Triggers Dokploy deployment webhook

### Environment Variables

Create a `.env` file or set in Dokploy:

```bash
# Database
MYSQL_ROOT_PASSWORD=secure-root-password
MYSQL_DATABASE=southeastarchers
MYSQL_USER=appuser
MYSQL_PASSWORD=secure-app-password

# Application
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key-here

# Email
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=noreply@southeastarchers.ie

# Sum Up Payment
SUMUP_API_KEY=your-sumup-api-key
SUMUP_MERCHANT_CODE=your-merchant-code

# Optional: Custom port
WEB_PORT=5000
```

## Architecture

### Services

1. **db** (MySQL 8.4)
   - Persistent storage via Docker volume
   - Health checks ensure availability before app starts
   - Exposed on port 3306 (configurable)

2. **redis** (Redis 7 Alpine)
   - Persistent storage for job queue
   - Health checks for reliability
   - Exposed on port 6379

3. **web** (Flask + Gunicorn)
   - Multi-stage build: assets built, then production image
   - Runs migrations automatically on startup
   - 4 Gunicorn workers with 120s timeout
   - Non-root user (appuser) for security
   - Exposes port 5000

4. **worker** (Python RQ)
   - Processes background jobs from Redis queue
   - Same codebase as web
   - Shares database and Redis with web service

### Development vs Production

| Feature | Development | Production |
|---------|------------|------------|
| Image | Dockerfile.dev | Dockerfile.web/worker |
| Reload | Hot reload enabled | Disabled |
| User | root | appuser (non-root) |
| Volumes | Code mounted | Code copied in image |
| Email | Mailhog | Real SMTP |
| Database | Hardcoded dev creds | Environment variables |
| Assets | Built on startup | Built during image build |

## Networking

All services communicate via the `app-network` bridge network. Services can reach each other using their service names:

- Web connects to database: `mysql+pymysql://user:pass@db:3306/dbname`
- Worker connects to Redis: `redis://redis:6379/0`
- Web sends email to Mailhog: `mailhog:1025` (dev only)

## Volumes

### Production
- `mysql_data` - Database persistence
- `redis_data` - Redis persistence

### Development
- `mysql_data_dev` - Database persistence
- `redis_data_dev` - Redis persistence
- Host code mounted at `/app` for hot-reload

## Troubleshooting

### Container won't start
```bash
# Check logs
make docker-logs

# Check specific service
docker-compose -f docker/docker-compose.dev.yml logs web
```

### Database connection issues
```bash
# Check database is healthy
docker-compose -f docker/docker-compose.dev.yml ps

# Check database logs
docker-compose -f docker/docker-compose.dev.yml logs db
```

### Port already in use
Change ports in docker-compose file or `.env`:
```bash
WEB_PORT=5001  # Change from 5000
```

### Permission issues
The development container runs as root to allow volume mounts. Production uses non-root user.

### Rebuild after dependency changes
```bash
make docker-rebuild
```

### Clean slate
```bash
# Stop and remove everything (including volumes)
docker-compose -f docker/docker-compose.dev.yml down -v

# Start fresh
make docker-up
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build images
        run: |
          docker-compose -f docker/docker-compose.yml build
      
      - name: Push to registry
        # Push to your registry
        
      - name: Deploy to Dokploy
        # Trigger Dokploy webhook
```

## Migration from Separate Services

If migrating from individual Dokploy services:

1. **Export data** from existing MySQL database
2. **Stop old services** in Dokploy
3. **Create new Compose app** pointing to this repository
4. **Import data** into new database
5. **Update DNS** to point to new service

## Benefits of Docker Compose

✅ **Simplified Development**: Single command to start everything
✅ **Environment Parity**: Dev matches production closely
✅ **Easy Onboarding**: New developers can start in minutes
✅ **Service Discovery**: Built-in networking between services
✅ **Health Checks**: Automatic restart and dependency management
✅ **Dokploy Native**: Dokploy has excellent Compose support

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Dokploy Documentation](https://docs.dokploy.com/)
- [Main README](../README.md)
