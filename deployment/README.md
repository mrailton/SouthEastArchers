# Docker Compose + Traefik Deployment Guide

Complete setup for deploying South East Archers with Docker Compose, Traefik, and Watchtower.

## Architecture

```
Internet
   │
   ▼
Traefik (Reverse Proxy + SSL)
   │
   ├─▶ southeastarchers.ie ─▶ sea-web:5000
   └─▶ traefik.yourdomain.com ─▶ Traefik Dashboard
                                    │
                                    ▼
                            sea-internal network
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                sea-web         sea-worker      sea-redis
                    │               │               │
                    └───────────────┴───────────────┘
                                    │
                                sea-db (MySQL)
```

## Features

- ✅ **Traefik**: Automatic HTTPS with Let's Encrypt
- ✅ **Watchtower**: Auto-updates containers from GHCR
- ✅ **Multi-app ready**: Easy to add more applications
- ✅ **Zero downtime**: Rolling updates
- ✅ **Scalable**: Scale workers easily
- ✅ **Monitoring**: Traefik dashboard

## Prerequisites

1. **Server** with Docker and Docker Compose installed
2. **Domain** pointed to your server IP
3. **Cloudflare** account (for DNS challenge, optional but recommended)
4. **GitHub** Container Registry access for images

## Quick Setup

### 1. Initial Setup

```bash
# On your server
cd /opt
git clone https://github.com/mrailton/SouthEastArchers.git
cd SouthEastArchers/deployment

# Login to GHCR (GitHub Container Registry)
chmod +x login-ghcr.sh
./login-ghcr.sh
# Enter your GitHub username and Personal Access Token

# Configure
cp .env.example .env
nano .env
```

### 2. Configure Environment

Edit `deployment/.env`:

```bash
# Your domain
DOMAIN=yourdomain.com

# Cloudflare (for automatic SSL)
CLOUDFLARE_EMAIL=your@email.com
CLOUDFLARE_DNS_API_TOKEN=your-api-token

# Traefik dashboard password
# Generate with:
chmod +x generate-traefik-auth.sh
./generate-traefik-auth.sh
# Then copy the output to .env file
TRAEFIK_DASHBOARD_CREDENTIALS=admin:$$2y$$05$$...

# Application secrets
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
MYSQL_ROOT_PASSWORD=strong-root-password
MYSQL_USER=sea_user
MYSQL_PASSWORD=strong-user-password
DATABASE_URL=mysql+pymysql://sea_user:strong-user-password@db:3306/southeastarchers

# Email config
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@southeastarchers.ie

# Payment
SUMUP_API_KEY=your-key
SUMUP_MERCHANT_CODE=your-code
```

### 3. Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

### 4. Initialize Application

```bash
# Run database migrations
docker exec sea-web flask db upgrade

# Create admin user
docker exec -it sea-web python manage.py create-admin
```

### 5. Verify Deployment

Visit:
- **Application**: https://southeastarchers.ie
- **Traefik Dashboard**: https://traefik.yourdomain.com

## Manual Setup (Alternative)

### 1. Create Docker Network

```bash
docker network create traefik
```

### 2. Setup Traefik

```bash
cd deployment/traefik

# Create SSL certificate storage
touch acme.json
chmod 600 acme.json

# Start Traefik
docker compose up -d

# Check logs
docker logs traefik -f
```

### 3. Deploy Application

```bash
cd ../southeastarchers

# Start all services
docker compose up -d

# Check status
docker ps
docker compose logs -f
```

## Management Commands

### View Logs

```bash
# All services
cd deployment/southeastarchers
docker compose logs -f

# Specific service
docker logs sea-web -f
docker logs sea-worker -f
docker logs traefik -f
```

### Restart Services

```bash
# All services
docker compose restart

# Specific service
docker compose restart web
docker compose restart worker
```

### Scale Workers

```bash
# Scale to 3 workers
docker compose up -d --scale worker=3

# Check running workers
docker ps | grep sea-worker
```

### Update Images (Manual)

```bash
# Pull latest images
docker compose pull

# Restart with new images
docker compose up -d

# Note: Watchtower does this automatically every 5 minutes
```

### Database Backup

```bash
# Backup
docker exec sea-db mysqldump -u root -p southeastarchers > backup.sql

# Restore
docker exec -i sea-db mysql -u root -p southeastarchers < backup.sql
```

### Check Watchtower Activity

```bash
docker logs sea-watchtower -f
```

## Adding More Applications

To add another application to the same server:

### 1. Create New App Directory

```bash
mkdir deployment/newapp
cd deployment/newapp
```

### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  newapp:
    image: ghcr.io/yourorg/newapp:latest
    container_name: newapp
    restart: unless-stopped
    networks:
      - traefik
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.newapp.entrypoints=http"
      - "traefik.http.routers.newapp.rule=Host(`newapp.yourdomain.com`)"
      - "traefik.http.middlewares.newapp-https-redirect.redirectscheme.scheme=https"
      - "traefik.http.routers.newapp.middlewares=newapp-https-redirect"
      - "traefik.http.routers.newapp-secure.entrypoints=https"
      - "traefik.http.routers.newapp-secure.rule=Host(`newapp.yourdomain.com`)"
      - "traefik.http.routers.newapp-secure.tls=true"
      - "traefik.http.routers.newapp-secure.tls.certresolver=cloudflare"
      - "traefik.http.routers.newapp-secure.service=newapp"
      - "traefik.http.services.newapp.loadbalancer.server.port=8080"
      - "traefik.docker.network=traefik"
      - "com.centurylinklabs.watchtower.enable=true"

networks:
  traefik:
    external: true
```

### 3. Deploy

```bash
docker compose up -d
```

Traefik automatically detects the new app and provisions SSL!

## Monitoring

### Check Service Health

```bash
# All containers
docker ps

# Service-specific health
docker inspect sea-web | grep -A 10 Health
```

### Resource Usage

```bash
docker stats
```

### Traefik Dashboard

Visit `https://traefik.yourdomain.com` to see:
- Active routers
- Services
- Middleware
- Certificate status
- Request metrics

## Troubleshooting

### SSL Certificate Issues

```bash
# Check certificate status
docker exec traefik cat /acme.json

# Remove and regenerate
rm traefik/acme.json
touch traefik/acme.json
chmod 600 traefik/acme.json
docker compose -f traefik/docker-compose.yml restart
```

### Service Not Accessible

```bash
# Check if service is running
docker ps | grep sea-web

# Check Traefik logs
docker logs traefik | grep sea-web

# Check labels are correct
docker inspect sea-web | grep traefik
```

### Worker Not Processing Jobs

```bash
# Check worker logs
docker logs sea-worker -f

# Check Redis connection
docker exec sea-redis redis-cli ping

# Check job queue
docker exec sea-redis redis-cli LLEN rq:queue:default
```

### Watchtower Not Updating

```bash
# Check Watchtower logs
docker logs sea-watchtower

# Manually trigger update
docker exec sea-watchtower watchtower --run-once
```

### Database Connection Issues

```bash
# Check MySQL is running
docker exec sea-db mysql -u root -p -e "SHOW DATABASES;"

# Check connection from web service
docker exec sea-web python -c "from app import db; print(db.engine)"
```

## Performance Tuning

### Adjust Worker Count

```bash
# Based on your traffic
docker compose up -d --scale worker=3
```

### Gunicorn Workers

Edit the web image CMD or override with docker-compose:

```yaml
services:
  web:
    command: gunicorn --bind 0.0.0.0:5000 --workers 8 --timeout 120 wsgi:app
```

### Redis Memory

```yaml
services:
  redis:
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## Security Best Practices

1. **Firewall**: Only expose ports 80 and 443
   ```bash
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw allow 22/tcp  # SSH
   ufw enable
   ```

2. **Docker Socket**: Don't expose to internet (Traefik handles it internally)

3. **Secrets**: Never commit `.env` files to git

4. **Updates**: Watchtower keeps containers updated automatically

5. **Backups**: Automate database backups
   ```bash
   # Add to crontab
   0 2 * * * docker exec sea-db mysqldump -u root -p southeastarchers > /backups/sea-$(date +\%Y\%m\%d).sql
   ```

## Cost Comparison

### vs Coolify
- **Pros**: More control, lighter weight, no platform overhead
- **Cons**: Manual setup, no web UI
- **Cost**: Free (just server costs)

### vs Kubernetes
- **Pros**: Simpler, less resource usage, easier to understand
- **Cons**: Less scalability features
- **Cost**: Can run on smaller servers

## Maintenance

### Weekly Tasks
- Check logs for errors
- Review resource usage
- Test backups

### Monthly Tasks
- Update server packages: `apt update && apt upgrade`
- Review Watchtower logs for update issues
- Check SSL certificate expiry (auto-renewed)

### Quarterly Tasks
- Review security settings
- Update Docker/Docker Compose
- Review and optimize resource allocation

## Support Resources

- Traefik Docs: https://doc.traefik.io/traefik/
- Watchtower Docs: https://containrrr.dev/watchtower/
- Docker Compose: https://docs.docker.com/compose/

## Migration from Coolify

If you're migrating from Coolify:

1. Export environment variables from Coolify
2. Backup database: `docker exec coolify-db mysqldump...`
3. Setup this stack following the guide
4. Restore database to new MySQL container
5. Update DNS to point to new server
6. Verify everything works
7. Decommission Coolify
