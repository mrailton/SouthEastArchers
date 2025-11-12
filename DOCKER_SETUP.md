# Docker Setup Summary

This document provides an overview of the Docker-based development setup for the SouthEast Archers application.

## 🎯 Overview

The project uses **Docker for local development** with:

- Hot reload for Python code changes
- Live CSS compilation with Tailwind
- Easy debugging and testing
- MySQL 8.0 database

For production deployment, only the production `Dockerfile` is used (no docker-compose).

## 📁 File Structure

```
.
├── Dockerfile                  # Production Dockerfile (Python 3.14)
├── Dockerfile.dev              # Development Dockerfile (Python 3.14)
├── docker-compose.yml          # Development docker-compose configuration
├── .dockerignore               # Files excluded from Docker builds
├── dev.sh                      # Development helper script
│
├── .env.example                # Production environment variables template
├── .env.dev.example            # Development environment variables template
│
├── DEVELOPMENT.md              # Complete development guide
├── DEPLOYMENT.md               # Production deployment guide
└── DOCKER_SETUP.md             # This file
```

## 🚀 Quick Start Commands

### Development

```bash
# Start everything
./dev.sh up

# Run migrations
./dev.sh migrate

# Create superuser
./dev.sh createsuperuser

# View logs
./dev.sh logs

# Stop
./dev.sh down
```

**Access**: http://localhost:8000

## 🔧 Development Environment

### Services

| Service | Port | Description |
|---------|------|-------------|
| **web** | 8000 | Django development server with hot reload |
| **db** | 3307 | MySQL 8.0 database |
| **tailwind** | - | Tailwind CSS watcher (background) |

### Features

✅ **Live Code Reload** - Changes to Python files reload automatically
✅ **Hot CSS Compilation** - Tailwind watches and recompiles CSS on change
✅ **Volume Mounts** - Source code mounted for instant changes
✅ **Fast Package Management** - uv for 10-100x faster installs
✅ **Debug Mode** - DEBUG=True, verbose errors, Django debug toolbar ready
✅ **Persistent Database** - Data survives container restarts

### Architecture

```
┌─────────────────────────────────────┐
│   Host Machine (localhost:8000)     │
└──────────────┬──────────────────────┘
               │
    ┌──────────▼──────────┐
    │  Docker Compose     │
    │  (Development)      │
    └─────────┬───────────┘
              │
    ┌─────────┴────────┬──────────┬──────────┐
    │                  │          │          │
┌───▼────┐      ┌─────▼──┐   ┌───▼──────┐  │
│  web   │◄─────┤   db   │   │ tailwind │  │
│        │      │        │   │          │  │
│ Django │      │ MySQL  │   │  watch   │  │
│  Dev   │      │  8.0   │   │   mode   │  │
│ Server │      │        │   │          │  │
└────────┘      └────────┘   └──────────┘  │
    │                                       │
    └───────────────────────────────────────┘
           Volume Mounts (Live Reload)
```

## 🏭 Production Deployment

Production uses the `Dockerfile` (not docker-compose) for deployment to platforms like Coolify, Railway, or other container hosting services.

### Production Features

✅ **Multi-stage Build** - Optimized image size (~471MB)
✅ **Multi-architecture** - ARM64 + x86_64 support
✅ **Production Server** - Gunicorn with 4 workers
✅ **Static Files** - WhiteNoise for efficient serving
✅ **Security** - Non-root user, health checks, security headers
✅ **Pre-compiled Assets** - Tailwind CSS built during image creation
✅ **GitHub Actions** - Automated multi-arch builds to GHCR

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment instructions.

## 🐍 Python 3.14

Both environments use **Python 3.14** for:
- Latest language features
- Performance improvements
- Security updates
- Future-proofing

## 📦 Package Management with uv

**uv** is 10-100x faster than pip:

```bash
# Add package
./dev.sh install requests

# Add dev dependency
./dev.sh install --dev pytest

# Add multiple packages
./dev.sh install requests beautifulsoup4

# Install specific version
./dev.sh install "django>=5.0,<6.0"
```

uv automatically:
- Updates `pyproject.toml`
- Updates `uv.lock`
- Rebuilds container
- Restarts service

## 🎨 Tailwind CSS

### Development
- **Automatic compilation** via dedicated container
- **Watch mode** - Recompiles on file changes
- **No manual build needed** - Just edit templates

### Production
- **Pre-compiled during build** - No Node.js in production image
- **Optimized for production** - Minified, compressed
- **Served by WhiteNoise** - Fast, efficient delivery

## 🗄️ Database

### Connection Details (Development)

- **Host**: localhost
- **Port**: 3307
- **Database**: southeast_archers
- **User**: root
- **Password**: devpassword (configurable in .env)

### MySQL Tools

```bash
# Database shell via dev.sh
./dev.sh dbshell

# Direct connection
mysql -h 127.0.0.1 -P 3307 -u root -pdevpassword southeast_archers

# Via Docker
docker-compose -f docker-compose.dev.yml exec db mysql -uroot -pdevpassword southeast_archers
```

### Data Persistence

Development data is stored in Docker volume `southeast_mysql_dev_data`.

To reset:
```bash
./dev.sh down
docker volume rm southeast_mysql_dev_data
./dev.sh up
./dev.sh migrate
```

## 🔐 Environment Variables

### Development (.env)

```bash
DEBUG=True
SECRET_KEY=dev-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DB_NAME=southeast_archers
DB_USER=root
MYSQL_ROOT_PASSWORD=devpassword
DB_HOST=db
DB_PORT=3306
```

### Production (Coolify)

```bash
DEBUG=False
SECRET_KEY=<strong-production-secret>
ALLOWED_HOSTS=yourdomain.com
DB_NAME=southeast_archers
DB_USER=django_user
DB_PASSWORD=<strong-password>
DB_HOST=<coolify-mysql-service>
DB_PORT=3306
```

## 📊 Development vs Production

| Feature | Development (docker-compose) | Production (Dockerfile) |
|---------|------------|------------|
| **Python** | 3.14 | 3.14 |
| **Server** | Django dev server | Gunicorn (4 workers) |
| **Reload** | Hot reload | Restart required |
| **DEBUG** | True | False |
| **Tailwind** | Watch mode | Pre-compiled |
| **Static Files** | Django serve | WhiteNoise |
| **Volume Mounts** | Yes (source code) | No (image only) |
| **Image Size** | ~800MB | ~471MB |
| **Build Time** | ~1 min | ~2-3 min |
| **Startup Time** | ~5 sec | ~3 sec |
| **Deployment** | Local only | Coolify/Railway/GHCR |

## 🛠️ Common Tasks

### Development Workflow

```bash
# Start your day
./dev.sh up

# Make code changes (auto-reload)
vim core/views.py

# Run tests
./dev.sh test

# Create migration
./dev.sh makemigrations

# Apply migration
./dev.sh migrate

# Install package
./dev.sh install django-debug-toolbar

# View logs
./dev.sh logs web

# Shell access
./dev.sh shell

# End your day
./dev.sh down
```

### Production Deployment

Production deployment doesn't use docker-compose. Instead:

```bash
# 1. Push to GitHub
git push origin main

# 2. GitHub Actions builds the production Docker image automatically
# Image: ghcr.io/<user>/southeast:latest

# 3. Deploy in Coolify or your hosting platform
# - Point to GHCR image or build from Dockerfile
# - Set environment variables
# - Run migrations
# - Done!
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 🧪 Testing

### Test Development Setup

```bash
# Build and start
./dev.sh up

# Check services
./dev.sh status

# Run migrations
./dev.sh migrate

# Create superuser
./dev.sh createsuperuser

# Access http://localhost:8000
# Should see homepage

# Check logs
./dev.sh logs
```

### Test Production Build Locally

To test the production Docker image locally before deploying:

```bash
# Build production image
docker build -t southeast:test .

# Run with environment variables
docker run -p 8000:8000 \
  -e DEBUG=False \
  -e SECRET_KEY=test-key \
  -e DB_HOST=host.docker.internal \
  southeast:test

# Check health
curl http://localhost:8000/health/
# Should return: {"status": "healthy"}
```

Note: You'll need a MySQL database accessible from the container for full testing.

## 🐛 Troubleshooting

### Port Conflicts

Change ports in `.env`:
```bash
WEB_PORT=8001
DB_PORT_HOST=3308
```

### Build Failures

```bash
# Clean build
./dev.sh clean
./dev.sh build

# Check Docker
docker system df
docker system prune -a
```

### Container Won't Start

```bash
# Check logs
./dev.sh logs

# Check specific service
./dev.sh logs web
./dev.sh logs db
./dev.sh logs tailwind
```

### Database Connection Issues

```bash
# Verify DB is healthy
./dev.sh status

# Check DB logs
./dev.sh logs db

# Test connection
./dev.sh dbshell
```

## 📚 Documentation

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Complete development guide with all commands
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment to Coolify
- **[README.md](README.md)** - Project overview and features

## 🎯 Best Practices

### Development

1. **Always use ./dev.sh** - Consistent, easy commands
2. **Keep containers running** - Fast iteration
3. **Use volume mounts** - No rebuild needed for code changes
4. **Check logs regularly** - `./dev.sh logs`
5. **Commit often** - Docker makes it safe to experiment

### Production

1. **Test production build locally first** - `docker build -t test .`
2. **Use environment variables** - Never hardcode secrets
3. **Review security settings** - settings.py production section
4. **Monitor logs** - Coolify/hosting platform dashboard
5. **Backup database** - Regular automated backups

## 🚀 Next Steps

1. **Start Development**
   ```bash
   ./dev.sh up
   ./dev.sh migrate
   ./dev.sh createsuperuser
   ```

2. **Read Full Docs**
   - [DEVELOPMENT.md](DEVELOPMENT.md) for detailed dev guide
   - [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment

3. **Deploy to Production**
   - Push to GitHub
   - Configure Coolify
   - Deploy!

## 🤝 Contributing

When adding features:
1. Work in development environment (`./dev.sh up`)
2. Test with `./dev.sh test`
3. Optionally test production build locally (`docker build -t test .`)
4. Push to GitHub for CI/CD to build production image

## 📝 Notes

- **Python 3.14** is the latest version
- **uv** manages all dependencies
- **Tailwind CSS** automatically compiles in both environments
- **Multi-architecture** support built-in
- **GitHub Actions** handles production builds
- **Coolify** for easy deployment

---

Happy coding! 🎉
