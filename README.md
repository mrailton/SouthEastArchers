# South East Archers - Membership & Events Portal

A modern web application for managing archery club memberships, shooting nights, and events built with Flask, MySQL, Tailwind CSS, and Alpine.js.

## Features

- **Public Website**: Information, news, and events pages
- **Member Portal**: Dashboard, shooting nights management, credit purchases, profile management
- **Admin Portal**: Membership management, shooting night recording, news and events management
- **Payment Processing**: Integration with Sum Up for membership and credit purchases
- **Authentication**: Email-based login with password reset functionality
- **Background Jobs**: Asynchronous email sending and scheduled tasks with Redis & RQ
- **Mobile Friendly**: Responsive design with Tailwind CSS 4.1
- **Docker Support**: Full Docker and Docker Compose setup for easy deployment

## Tech Stack

- **Backend**: Flask 3.0.0 with Python 3.14
- **Database**: MySQL 8.4
- **Background Jobs**: Redis + RQ for async task processing
- **Frontend**: Tailwind CSS 4.1 + Alpine.js 3
- **Asset Pipeline**: Webassets with minification
- **Testing**: pytest with comprehensive coverage
- **Deployment**: Docker + Coolify
- **Email**: SMTP for password resets and notifications
- **Payments**: Sum Up API

## Quick Start

### Docker Development (Recommended)

The easiest way to get started is using Docker Compose:

```bash
# Start everything (MySQL, Redis, Web, Worker, Mailhog)
make docker-up

# View logs
make docker-logs

# Stop everything
make docker-down
```

Visit:
- Application: http://localhost:5000
- Email testing (Mailhog): http://localhost:8025

**Features:**
- No local dependencies needed (Python, Node, MySQL, Redis all in containers)
- Hot reload for code changes
- Auto-restart for background worker
- Email testing with Mailhog

See [docker/README.md](docker/README.md) for detailed Docker documentation.

### Local Development (Without Docker)

```bash
# Install dependencies
make install

# Start Redis (for background jobs)
docker run -d -p 6379:6379 redis:7-alpine

# Start worker (in separate terminal)
make worker-dev

# Run development server
make dev
```

Visit http://localhost:5000

## Deployment

### Dokploy with Docker Compose (Recommended)

This project uses Docker Compose with pre-built images from GitHub Container Registry (GHCR).

**Quick Deploy to Dokploy:**

1. **Create a Compose Application** in Dokploy
2. **Connect your Git repository**
3. **Set compose file path** to `docker/docker-compose.yml`
4. **Add environment variables** (see `.env.example`)
   - Database credentials
   - Flask SECRET_KEY
   - Email (SMTP) settings
   - Sum Up payment API keys
5. **Deploy!**

Dokploy will automatically:
- Pull pre-built images from GHCR (fast, no build step!)
- Start MySQL and Redis
- Run database migrations
- Expose your application

**How CI/CD Works:**
- Push to `main` → GitHub Actions builds images → Pushes to GHCR → Dokploy pulls latest
- Images: `ghcr.io/mrailton/southeastarchers-web:latest` and `southeastarchers-worker:latest`

**Detailed Guide**: See [docs/DOKPLOY_DEPLOYMENT.md](docs/DOKPLOY_DEPLOYMENT.md) for comprehensive deployment documentation.

### Alternative: GitHub Actions + GHCR (Legacy)

Images can be automatically built and pushed to GitHub Container Registry (GHCR) on every push to main.

**Full deployment guide**: [docs/COOLIFY_DEPLOYMENT.md](docs/COOLIFY_DEPLOYMENT.md)

**Quick Deploy:**
1. GitHub Actions builds and pushes images to GHCR
2. Configure Dokploy to pull from GHCR
3. Set environment variables
4. Deploy

### Manual Docker

```bash
# Using Docker Compose (Production)
cd docker
docker-compose up -d

# Or build individual images
docker build -f docker/Dockerfile.web -t sea-app .
docker build -f docker/Dockerfile.worker -t sea-worker .

# Run web server
docker run -p 5000:5000 --env-file .env sea-app

# Run worker
docker run --env-file .env sea-worker
```

## Development Commands

```bash
# Docker (Recommended)
make docker-up        # Start all services with Docker Compose
make docker-down      # Stop all services
make docker-logs      # View logs
make docker-rebuild   # Rebuild containers
make docker-shell     # Open shell in web container

# Local Development (Without Docker)
make help             # Show all available commands
make install          # Install all dependencies
make dev              # Run dev server + asset watcher
make test             # Run test suite
make test-cov         # Run tests with coverage
make worker-dev       # Start worker with auto-reload
make format           # Format code
make format-check     # Check code quality
```

## Documentation

- [Docker Setup Guide](docker/README.md) - Comprehensive Docker Compose documentation
- [Dokploy Deployment Guide](docs/DOKPLOY_DEPLOYMENT.md) - Step-by-step deployment to Dokploy
- [GHCR Integration Guide](docs/GHCR_INTEGRATION.md) - Using GitHub Container Registry
- [Docker Migration Notes](docs/DOCKER_MIGRATION.md) - What changed in the Docker setup
- [Background Jobs Guide](docs/BACKGROUND_JOBS.md) - Redis & RQ setup

## License

MIT
