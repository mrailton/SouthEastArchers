# Deployment Guide

This guide covers deploying the South East Archers application using Docker and GitHub Container Registry (GHCR).

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [GitHub Actions Setup](#github-actions-setup)
- [Manual Docker Build](#manual-docker-build)
- [Deployment Options](#deployment-options)
- [Configuration](#configuration)
- [Monitoring](#monitoring)

## Prerequisites

### Required
- Docker 20.10+ and Docker Compose 2.0+
- GitHub account with repository access
- Domain name (for production with SSL)

### Optional
- Nginx (if not using Docker Compose with nginx profile)
- PostgreSQL (recommended for production)

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/SouthEastArchers.git
cd SouthEastArchers

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Run with Docker Compose

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The application will be available at http://localhost:5000

### 3. Initialize Database

```bash
# Run database migrations
docker-compose exec web flask db upgrade

# Create sample data (optional)
docker-compose exec web python create_sample_data.py
```

## GitHub Actions Setup

### 1. Enable GitHub Container Registry

1. Go to your repository settings
2. Navigate to "Actions" → "General"
3. Scroll to "Workflow permissions"
4. Select "Read and write permissions"
5. Check "Allow GitHub Actions to create and approve pull requests"
6. Save changes

### 2. Repository Secrets (Optional)

For additional services, add these secrets in Settings → Secrets → Actions:

- `CODECOV_TOKEN` - For code coverage reporting (optional)
- `SLACK_WEBHOOK` - For deployment notifications (optional)

### 3. Workflow Triggers

The Docker build workflow runs on:
- **Push to main/develop** - Builds and pushes image with branch tag
- **Pull requests** - Builds image (doesn't push)
- **Tags (v*)** - Builds and pushes with version tags
- **Manual trigger** - Via GitHub Actions UI

### 4. Image Tags

Images are tagged automatically:
- `latest` - Latest build from main branch
- `main`, `develop` - Branch name
- `v1.0.0`, `v1.0`, `v1` - Semantic version tags
- `main-abc123` - Branch name with commit SHA

## Manual Docker Build

### Build Locally

```bash
# Build the image
docker build -t southeastarchers:latest .

# Run the container
docker run -d \
  -p 5000:5000 \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=sqlite:///instance/app.db \
  -v $(pwd)/instance:/app/instance \
  --name southeastarchers \
  southeastarchers:latest
```

### Push to GHCR

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Tag the image
docker tag southeastarchers:latest ghcr.io/USERNAME/southeastarchers:latest

# Push the image
docker push ghcr.io/USERNAME/southeastarchers:latest
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

Best for: Development, small deployments

```bash
# Basic deployment
docker-compose up -d

# With Nginx reverse proxy
docker-compose --profile with-nginx up -d
```

### Option 2: Docker Swarm

Best for: Multi-node deployments, high availability

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml southeastarchers

# Scale services
docker service scale southeastarchers_web=3
```

### Option 3: Kubernetes

Best for: Large-scale, enterprise deployments

```bash
# Apply configurations
kubectl apply -f k8s/

# Check status
kubectl get pods -n southeastarchers
```

### Option 4: Cloud Platforms

#### Railway

1. Connect GitHub repository
2. Set environment variables
3. Deploy automatically from main branch

#### Render

1. Create new Web Service
2. Connect GitHub repository
3. Docker detection is automatic
4. Set environment variables

#### DigitalOcean App Platform

1. Create new app
2. Connect GitHub repository
3. Select Dockerfile
4. Configure environment

## Configuration

### Environment Variables

Required:
```env
SECRET_KEY=your-random-secret-key
DATABASE_URL=sqlite:///instance/app.db
```

Optional:
```env
FLASK_ENV=production
CREDIT_COST=5.00
```

### Database Options

#### SQLite (Development)
```env
DATABASE_URL=sqlite:///instance/app.db
```

#### PostgreSQL (Production Recommended)
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

#### MySQL
```env
DATABASE_URL=mysql+pymysql://user:password@host:3306/dbname
```

### SSL/TLS Setup

#### Option 1: Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

#### Option 2: Self-Signed (Development Only)

```bash
# Create SSL directory
mkdir -p nginx/ssl

# Generate certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

## Production Checklist

### Security
- [ ] Change SECRET_KEY to a strong random value
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Set up firewall rules
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable Docker security scanning
- [ ] Regular security updates

### Performance
- [ ] Configure proper number of Gunicorn workers
- [ ] Set up connection pooling for database
- [ ] Enable caching (Redis/Memcached)
- [ ] Configure CDN for static files
- [ ] Set up load balancing if needed

### Reliability
- [ ] Configure automatic backups
- [ ] Set up monitoring and alerts
- [ ] Configure log aggregation
- [ ] Test disaster recovery procedures
- [ ] Document runbooks

### Monitoring
- [ ] Application logs
- [ ] Error tracking (e.g., Sentry)
- [ ] Performance monitoring (e.g., New Relic)
- [ ] Uptime monitoring
- [ ] Resource usage tracking

## Monitoring

### View Logs

```bash
# Application logs
docker-compose logs -f web

# All services
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Health Checks

```bash
# Check container health
docker-compose ps

# Manual health check
curl http://localhost:5000/

# Container stats
docker stats southeastarchers
```

### Database Backups

```bash
# Backup SQLite
docker-compose exec web sh -c 'cp instance/app.db /tmp/backup.db'
docker cp southeastarchers:/tmp/backup.db ./backup-$(date +%Y%m%d).db

# Backup PostgreSQL
docker-compose exec postgres pg_dump -U user dbname > backup.sql
```

## Troubleshooting

### Common Issues

**Container won't start**
```bash
# Check logs
docker-compose logs web

# Verify environment variables
docker-compose config
```

**Database migrations fail**
```bash
# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec web flask db upgrade
```

**Permission errors**
```bash
# Fix volume permissions
sudo chown -R 1000:1000 instance/
```

**Port already in use**
```bash
# Find process using port
lsof -i :5000

# Change port in docker-compose.yml
ports:
  - "8080:5000"
```

## Updating

### Pull Latest Image

```bash
# Pull latest from GHCR
docker pull ghcr.io/USERNAME/southeastarchers:latest

# Restart services
docker-compose up -d
```

### Update from Source

```bash
# Pull latest code
git pull origin main

# Rebuild image
docker-compose build

# Restart
docker-compose up -d

# Run migrations
docker-compose exec web flask db upgrade
```

## Rollback

```bash
# List available tags
docker images ghcr.io/USERNAME/southeastarchers

# Use specific version
docker-compose down
export IMAGE_TAG=v1.0.0
docker-compose up -d
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/USERNAME/SouthEastArchers/issues
- Documentation: README.md
- Security: SECURITY.md (if applicable)

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Flask Deployment](https://flask.palletsprojects.com/en/latest/deploying/)
- [Gunicorn](https://docs.gunicorn.org/)
