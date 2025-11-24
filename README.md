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

### Local Development

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

### Coolify with GitHub Actions + GHCR (Recommended)

Images are automatically built and pushed to GitHub Container Registry (GHCR) on every push to main.

**Full deployment guide**: [docs/COOLIFY_DEPLOYMENT.md](docs/COOLIFY_DEPLOYMENT.md)

**Quick Reference**: [COOLIFY_QUICK_DEPLOY.md](COOLIFY_QUICK_DEPLOY.md)

**Quick Deploy:**
1. Create 4 services in Coolify:
   - MySQL Database (managed)
   - Redis Database (managed)
   - Web Application (Docker Image: `ghcr.io/mrailton/southeastarchers-web:latest`)
   - Worker (Docker Image: `ghcr.io/mrailton/southeastarchers-worker:latest`)
2. Add environment variables to each service (see `.env.example`)
3. Configure webhook for auto-deploy
4. Push to main → GitHub Actions builds → Coolify deploys!

**What happens on deployment:**
- GitHub Actions runs tests
- Builds Docker images for web and worker
- Pushes images to GHCR
- Triggers Coolify webhook
- Coolify pulls latest images and restarts services

### Manual Docker

```bash
# Build images
docker build -f Dockerfile.web -t sea-app .
docker build -f Dockerfile.worker -t sea-worker .

# Run web server
docker run -p 5000:5000 --env-file .env sea-app

# Run worker
docker run --env-file .env sea-worker
```

## Development Commands

```bash
make help           # Show all available commands
make install        # Install all dependencies
make dev            # Run dev server + asset watcher
make test           # Run test suite
make test-cov       # Run tests with coverage
make worker         # Start RQ worker
make worker-dev     # Start worker with auto-reload
make format         # Format code
make format-check   # Check code quality
```

## Documentation

- [Background Jobs Guide](docs/BACKGROUND_JOBS.md) - Redis & RQ setup
- [Coolify Deployment](docs/COOLIFY_DEPLOYMENT.md) - Production deployment guide

## License

MIT
