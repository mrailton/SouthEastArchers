# Deployment Guide for Coolify

This guide covers deploying the SouthEast Archers Django application using Coolify with Docker images built via GitHub Actions.

> **For local development**, see [DEVELOPMENT.md](DEVELOPMENT.md) for Docker-based development setup with live reload and uv package management.

## Architecture

- **Python Version**: 3.14
- **Package Manager**: uv (10-100x faster than pip)
- **Docker Image**: Multi-architecture (ARM64 & AMD64) built via GitHub Actions
- **Container Registry**: GitHub Container Registry (GHCR)
- **Web Server**: Gunicorn with 4 workers
- **Static Files**: Served by WhiteNoise
- **Database**: MySQL 8.0
- **Orchestration**: Coolify

## Prerequisites

1. GitHub repository with Actions enabled
2. Coolify instance running
3. MySQL database (can be created in Coolify)

## Setup Instructions

### 1. Configure GitHub Container Registry

The GitHub Actions workflow is already configured to push to GHCR. It uses the built-in `GITHUB_TOKEN` secret, so no additional configuration is needed.

**Image will be available at:**
```
ghcr.io/<your-username>/southeast
```

### 2. Enable GitHub Actions

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Actions** → **General**
3. Ensure "Allow all actions and reusable workflows" is selected
4. Go to **Settings** → **Actions** → **Workflow permissions**
5. Select "Read and write permissions"
6. Check "Allow GitHub Actions to create and approve pull requests"

### 3. Make Registry Public (or use authentication)

#### Option A: Public Registry (Easier)
1. Go to your repository on GitHub
2. Navigate to **Packages** (right sidebar)
3. Click on your package
4. Click **Package settings**
5. Scroll down to **Danger Zone**
6. Click **Change visibility** → **Public**

#### Option B: Private Registry (More Secure)
Create a Personal Access Token (PAT) with `read:packages` scope and use it in Coolify.

### 4. Set Up in Coolify

#### Create the Application

1. Log in to your Coolify instance
2. Create a new project or select an existing one
3. Click **+ New Resource** → **Application**
4. Select **Docker Image** as source
5. Configure:
   - **Name**: `southeast-archers`
   - **Image**: `ghcr.io/<your-username>/southeast:latest`
   - **Port**: `8000`
   - **Pull Request on Deploy**: Enable

#### Configure Environment Variables

Add the following environment variables in Coolify:

```env
# Django Core
DEBUG=False
SECRET_KEY=<generate-a-strong-secret-key>
ALLOWED_HOSTS=<your-domain.com>

# Database (use Coolify's MySQL service)
DB_NAME=southeast_archers
DB_USER=django_user
DB_PASSWORD=<strong-password>
DB_HOST=<coolify-mysql-service-name>
DB_PORT=3306

# Security (optional - defaults to True in production)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

#### Set Up MySQL Database in Coolify

1. In the same project, click **+ New Resource** → **Database**
2. Select **MySQL 8.0**
3. Configure:
   - **Name**: `southeast-db`
   - **Root Password**: Generate a strong password
4. After creation, create the application database:
   - Connect to the database console
   - Run: `CREATE DATABASE southeast_archers CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
   - Run: `CREATE USER 'django_user'@'%' IDENTIFIED BY '<password>';`
   - Run: `GRANT ALL PRIVILEGES ON southeast_archers.* TO 'django_user'@'%';`
   - Run: `FLUSH PRIVILEGES;`

#### Configure Persistent Storage

Add persistent volumes for:
- **Media files**: Mount `/app/media` to a persistent volume
- **Static files**: Optional (generated during build, but can be persisted for faster deployments)

#### Set Up Domain

1. In the application settings, go to **Domains**
2. Add your domain: `southeast.yourdomain.com`
3. Enable **HTTPS** (Coolify will handle Let's Encrypt automatically)

### 5. Deploy

#### Initial Deployment

1. Push your code to the `main` branch
2. GitHub Actions will automatically build and push the Docker image
3. In Coolify, click **Deploy** or enable **Auto Deploy** from the Git repository

#### Run Migrations

After first deployment, run migrations:
1. Go to your application in Coolify
2. Open the **Terminal** tab
3. Run:
```bash
python manage.py migrate
```

#### Create Superuser

In the Coolify terminal:
```bash
python manage.py createsuperuser
```

### 6. Automatic Deployments

The workflow triggers automatically on:
- Push to `main` branch
- Push to `develop` branch
- New tags (e.g., `v1.0.0`)

Coolify can be configured to:
- Watch for new images with specific tags
- Auto-deploy when a new image is pushed
- Set up webhooks for instant deployments

## Local Development vs Production Testing

### Local Development

For daily development with live reload and hot module replacement:

```bash
# See DEVELOPMENT.md for full guide
./dev.sh up
./dev.sh migrate
./dev.sh createsuperuser
```

### Production Testing

Test the production Docker setup locally before deploying:

```bash
# Build and run with production configuration
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

The production setup uses:
- Gunicorn instead of Django dev server
- Pre-compiled Tailwind CSS
- DEBUG=False by default
- Optimized multi-stage build

## Multi-Architecture Build

The GitHub Actions workflow builds for both architectures:
- `linux/amd64` (x86_64) - Most cloud servers
- `linux/arm64` (ARM64) - ARM-based servers, Apple Silicon

Docker will automatically pull the correct architecture for your server.

## Health Checks

The application includes a health check endpoint:
- **URL**: `/health/`
- **Response**: `{"status": "healthy"}`

The Dockerfile includes a `HEALTHCHECK` instruction that Coolify will use to monitor application health.

## Troubleshooting

### Image Build Fails

Check GitHub Actions logs:
1. Go to **Actions** tab in your repository
2. Click on the failed workflow
3. Review the logs for errors

### Container Won't Start

Check logs in Coolify:
1. Go to application **Logs** tab
2. Look for Python errors or missing environment variables

### Database Connection Issues

1. Verify DB_HOST matches your MySQL service name in Coolify
2. Check database credentials
3. Ensure MySQL service is running and healthy
4. Test connection from application terminal:
```bash
python manage.py dbshell
```

### Static Files Not Loading

1. Ensure WhiteNoise is in MIDDLEWARE (already configured)
2. Check STATIC_ROOT is set correctly
3. Rebuild image (static files are collected during build)

## Updating the Application

1. Push changes to GitHub
2. GitHub Actions builds new image
3. Coolify detects new image and redeploys (if auto-deploy enabled)
4. Or manually click **Deploy** in Coolify

## Rollback

In Coolify:
1. Go to **Deployments** tab
2. Find previous successful deployment
3. Click **Rollback** or **Redeploy**

## Security Checklist

- [ ] Change SECRET_KEY to a strong random value
- [ ] Set DEBUG=False in production
- [ ] Configure ALLOWED_HOSTS with your domain
- [ ] Use strong database passwords
- [ ] Enable HTTPS in Coolify
- [ ] Set up regular database backups
- [ ] Review and configure security headers (already included when DEBUG=False)
- [ ] Set up monitoring and alerts in Coolify

## Performance Tuning

### Gunicorn Workers

Edit `Dockerfile` CMD to adjust workers:
```dockerfile
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

Formula: `(2 × CPU cores) + 1`

### Database Connection Pooling

Consider adding persistent database connections in settings.py:
```python
DATABASES = {
    'default': {
        # ... existing config
        'CONN_MAX_AGE': 600,  # 10 minutes
    }
}
```

## Monitoring

Coolify provides built-in monitoring for:
- CPU usage
- Memory usage
- Container health
- Application logs

Consider adding:
- Sentry for error tracking
- Application performance monitoring (APM)
- Database query monitoring

## Backup Strategy

1. **Database**: Use Coolify's built-in MySQL backup feature
2. **Media Files**: Backup the persistent volume regularly
3. **Configuration**: Keep `.env` backup in secure location

## Support

For issues:
- GitHub Actions: Check repository Actions tab
- Coolify: Check application logs and Coolify documentation
- Django: Review application logs in Coolify terminal
