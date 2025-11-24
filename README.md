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

### Docker Compose

```bash
# Start all services (web, worker, redis, db)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Deployment

### Coolify (Recommended)

Full deployment guide: [docs/COOLIFY_DEPLOYMENT.md](docs/COOLIFY_DEPLOYMENT.md)

**Quick Deploy:**
1. Create new project in Coolify → Docker Compose
2. Connect your GitHub repository
3. Add environment variables (see `.env.example`)
4. Deploy!

Coolify will automatically deploy:
- Web application (Flask + Gunicorn)
- Background workers (RQ)
- Redis (job queue)
- MySQL database (separate service)

### Manual Docker

```bash
# Build image
docker build -t sea-app .

# Run web server
docker run -p 5000:5000 --env-file .env sea-app

# Run worker
docker run --env-file .env sea-app uv run python worker.py
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
