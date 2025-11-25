# Dokku Deployment Guide for South East Archers

Complete guide for deploying with Dokku - the simplest self-hosted PaaS.

## What is Dokku?

Dokku is a Docker-powered mini-Heroku. You `git push` and it automatically:
- Builds your app
- Creates containers
- Sets up routing & SSL
- Manages databases

## Architecture

```
Your Local Machine                    Dokku Server
       │                                    │
       │  git push dokku main               │
       ├───────────────────────────────────>│
       │                                    │
       │                                    ├─> Build image
       │                                    ├─> Deploy web
       │                                    ├─> Deploy workers
       │                                    ├─> Setup SSL (Let's Encrypt)
       │                                    └─> Live! ✨
```

## Prerequisites

1. **Server** with Ubuntu 20.04/22.04/24.04
2. **Domain** pointed to server IP
3. **SSH access** to server

## Server Setup

### 1. Install Dokku

```bash
# SSH into your server
ssh root@your-server

# Install Dokku (latest version)
wget -NP . https://dokku.com/install/v0.35.11/bootstrap.sh
sudo DOKKU_TAG=v0.35.11 bash bootstrap.sh

# Setup domain (optional but recommended)
dokku domains:set-global yourdomain.com

# Install Let's Encrypt plugin
sudo dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git
```

### 2. Setup SSH Keys

```bash
# On your local machine, copy your public key
cat ~/.ssh/id_rsa.pub

# On server, add your key
echo "YOUR_PUBLIC_KEY_HERE" | dokku ssh-keys:add admin
```

### 3. Create Apps

```bash
# Main web application
dokku apps:create sea-web

# Worker application
dokku apps:create sea-worker
```

### 4. Create Databases

```bash
# Install MySQL plugin
sudo dokku plugin:install https://github.com/dokku/dokku-mysql.git mysql

# Install Redis plugin
sudo dokku plugin:install https://github.com/dokku/dokku-redis.git redis

# Create MySQL database
dokku mysql:create sea-db

# Create Redis instance
dokku redis:create sea-redis

# Link to apps
dokku mysql:link sea-db sea-web
dokku mysql:link sea-db sea-worker
dokku redis:link sea-redis sea-web
dokku redis:link sea-redis sea-worker
```

### 5. Configure Environment Variables

```bash
# Web app config
dokku config:set sea-web \
  FLASK_ENV=production \
  SECRET_KEY=$(openssl rand -hex 32) \
  MAIL_SERVER=smtp.gmail.com \
  MAIL_PORT=587 \
  MAIL_USE_TLS=True \
  MAIL_USERNAME=your@gmail.com \
  MAIL_PASSWORD=your-app-password \
  MAIL_DEFAULT_SENDER=noreply@southeastarchers.ie \
  SUMUP_API_KEY=your-key \
  SUMUP_MERCHANT_CODE=your-code

# Worker config (same as web)
dokku config:set sea-worker \
  FLASK_ENV=production \
  SECRET_KEY=$(openssl rand -hex 32) \
  MAIL_SERVER=smtp.gmail.com \
  MAIL_PORT=587 \
  MAIL_USE_TLS=True \
  MAIL_USERNAME=your@gmail.com \
  MAIL_PASSWORD=your-app-password \
  MAIL_DEFAULT_SENDER=noreply@southeastarchers.ie
```

### 6. Setup Domains

```bash
# Set domain for web app
dokku domains:add sea-web southeastarchers.ie
dokku domains:add sea-web www.southeastarchers.ie

# Enable SSL
dokku letsencrypt:enable sea-web
dokku letsencrypt:cron-job --add sea-web
```

### 7. Configure Port Mapping

```bash
# Web app listens on port 5000
dokku ports:add sea-web http:80:5000
dokku ports:add sea-web https:443:5000

# Worker doesn't need ports (background only)
dokku ports:clear sea-worker
```

## Deploy Method: Using GHCR Images

Since you already have GitHub Actions building Docker images, we'll configure Dokku to pull from GHCR instead of building from source.

### 1. Login to GHCR on Server

```bash
# SSH into server
ssh root@your-server

# Login to GitHub Container Registry
docker login ghcr.io -u YOUR_GITHUB_USERNAME -p YOUR_GITHUB_PAT

# Create directory for credentials
mkdir -p /root/.docker
```

### 2. Create Apps

```bash
# Create apps
dokku apps:create sea-web
dokku apps:create sea-worker

# Configure to use Docker images (not buildpacks)
dokku builder:set sea-web selected docker-image
dokku builder:set sea-worker selected docker-image

# Set the image sources
dokku git:set sea-web deploy-branch main
dokku git:set sea-worker deploy-branch main
```

### 3. Deploy from GHCR

```bash
# Deploy web app from GHCR
dokku git:from-image sea-web ghcr.io/mrailton/southeastarchers:latest

# Deploy worker app from GHCR
dokku git:from-image sea-worker ghcr.io/mrailton/southeastarchers-worker:latest

# Scale workers (run 2 instances)
dokku ps:scale sea-worker worker=2
```

### 4. Setup Auto-Deploy Webhook

To automatically deploy when new images are pushed to GHCR, create a webhook.

```bash
# Get the deploy webhook URL
dokku git:public-key sea-web

# In your GitHub repo settings:
# Settings → Webhooks → Add webhook
# Payload URL: http://your-server:3000/deploy/sea-web
# Content type: application/json
# Secret: (leave empty or set one)
# Events: Package published

# Or use GitHub Actions to trigger deploy
```

### 5. Configure GitHub Actions to Trigger Dokku Deploy

Add to `.github/workflows/ci.yml` after image push:

```yaml
- name: Deploy to Dokku
  if: github.ref == 'refs/heads/main'
  run: |
    curl -X POST https://your-server/deploy/sea-web \
      -H "Authorization: Bearer ${{ secrets.DOKKU_DEPLOY_TOKEN }}"
    curl -X POST https://your-server/deploy/sea-worker \
      -H "Authorization: Bearer ${{ secrets.DOKKU_DEPLOY_TOKEN }}"
```

Or use SSH to trigger deploy:

```yaml
- name: Deploy to Dokku
  if: github.ref == 'refs/heads/main'
  uses: appleboy/ssh-action@master
  with:
    host: ${{ secrets.DOKKU_HOST }}
    username: dokku
    key: ${{ secrets.DOKKU_SSH_KEY }}
    script: |
      dokku git:from-image sea-web ghcr.io/mrailton/southeastarchers:latest
      dokku git:from-image sea-worker ghcr.io/mrailton/southeastarchers-worker:latest
      dokku ps:scale sea-worker worker=2
```

### Run Database Migrations

```bash
# Run migrations on web app
ssh dokku@your-server run sea-web flask db upgrade

# Create admin user
ssh dokku@your-server run sea-web python manage.py create-admin
```

## Post-Deployment

### Check Status

```bash
# View all apps
ssh dokku@your-server apps:list

# View app info
ssh dokku@your-server apps:info sea-web

# Check running processes
ssh dokku@your-server ps:report sea-web
```

### View Logs

```bash
# Web logs
ssh dokku@your-server logs sea-web -t

# Worker logs
ssh dokku@your-server logs sea-worker -t

# Database logs
ssh dokku@your-server mysql:logs sea-db -t
```

### Scale Workers

```bash
# Scale to 3 workers
ssh dokku@your-server ps:scale sea-worker worker=3

# Check scaling
ssh dokku@your-server ps:report sea-worker
```

## Maintenance

### Update Application

```bash
# GitHub Actions builds new images on push to main
# Then manually trigger deploy on server:
ssh dokku@your-server git:from-image sea-web ghcr.io/mrailton/southeastarchers:latest
ssh dokku@your-server git:from-image sea-worker ghcr.io/mrailton/southeastarchers-worker:latest

# Or automate via GitHub Actions (see Deploy section)
# Dokku redeploys with zero downtime
```

### Database Backup

```bash
# Export database
ssh dokku@your-server mysql:export sea-db > backup.sql

# Import database
ssh dokku@your-server mysql:import sea-db < backup.sql
```

### Restart Services

```bash
# Restart web
ssh dokku@your-server ps:restart sea-web

# Restart worker
ssh dokku@your-server ps:restart sea-worker
```

### Environment Variables

```bash
# View config
ssh dokku@your-server config:show sea-web

# Update config
ssh dokku@your-server config:set sea-web KEY=value

# Remove config
ssh dokku@your-server config:unset sea-web KEY
```

## Troubleshooting

### Build Fails

```bash
# Check build logs
ssh dokku@your-server logs sea-web --tail 100

# Rebuild
ssh dokku@your-server ps:rebuild sea-web
```

### App Not Starting

```bash
# Check if app is running
ssh dokku@your-server ps:report sea-web

# Check logs
ssh dokku@your-server logs sea-web -t

# Restart
ssh dokku@your-server ps:restart sea-web
```

### Database Connection Issues

```bash
# Check database is running
ssh dokku@your-server mysql:info sea-db

# Check connection string
ssh dokku@your-server config:get sea-web DATABASE_URL

# Test connection
ssh dokku@your-server run sea-web python -c "from app import db; print(db.engine)"
```

### SSL Certificate Issues

```bash
# Renew certificate
ssh dokku@your-server letsencrypt:enable sea-web

# Check certificate status
ssh dokku@your-server letsencrypt:list
```

## Advanced Features

### Zero Downtime Deployments

Dokku does this automatically! It:
1. Builds new version
2. Starts new containers
3. Health checks pass
4. Routes traffic to new version
5. Stops old containers

### Persistent Storage

```bash
# Create storage directory
ssh dokku@your-server storage:ensure-directory sea-web

# Mount storage
ssh dokku@your-server storage:mount sea-web /var/lib/dokku/data/storage/sea-web:/app/storage
```

### Custom Checks

Create `CHECKS` file in project root:

```
WAIT=5
ATTEMPTS=12
/
```

Dokku will wait for app to respond on `/` before routing traffic.

### Scheduled Tasks (Cron)

```bash
# Install cron plugin
ssh dokku@your-server plugin:install https://github.com/dokku/dokku-cron.git

# Add cron job (check expiring memberships daily at 2am)
ssh dokku@your-server cron:set sea-worker "0 2 * * *" python manage.py check-expiring-memberships
```

## Cost Comparison

### vs Coolify
- **Pros**: Simpler, lighter, Heroku-like workflow
- **Cons**: No web UI, less features
- **Cost**: Free (just server costs)

### vs Docker Compose + Traefik
- **Pros**: Much simpler deployment, automatic SSL, zero-downtime deploys
- **Cons**: Less control over infrastructure
- **Cost**: Same (just server costs)

### vs Heroku
- **Pros**: Self-hosted (you own it), no platform fees
- **Cons**: You manage the server
- **Cost**: Much cheaper (1 server vs per-app pricing)

## Useful Commands

```bash
# List all commands
ssh dokku@your-server help

# App management
ssh dokku@your-server apps:list
ssh dokku@your-server apps:info sea-web
ssh dokku@your-server apps:destroy sea-web

# Database management
ssh dokku@your-server mysql:list
ssh dokku@your-server mysql:info sea-db
ssh dokku@your-server mysql:logs sea-db -t

# Redis management
ssh dokku@your-server redis:list
ssh dokku@your-server redis:info sea-redis

# Process management
ssh dokku@your-server ps:report
ssh dokku@your-server ps:scale sea-worker worker=3
ssh dokku@your-server ps:restart sea-web

# SSL/Let's Encrypt
ssh dokku@your-server letsencrypt:list
ssh dokku@your-server letsencrypt:enable sea-web
ssh dokku@your-server letsencrypt:cron-job --add sea-web

# Logs
ssh dokku@your-server logs sea-web -t
ssh dokku@your-server logs sea-worker -t

# Run commands
ssh dokku@your-server run sea-web flask db upgrade
ssh dokku@your-server run sea-web python manage.py create-admin

# Configuration
ssh dokku@your-server config:show sea-web
ssh dokku@your-server config:set sea-web KEY=value
ssh dokku@your-server config:unset sea-web KEY
```

## Quick Deployment Checklist

- [ ] Dokku installed on server
- [ ] Docker logged into GHCR on server
- [ ] SSH keys configured
- [ ] Apps created (`sea-web`, `sea-worker`)
- [ ] Builder set to `docker-image` for both apps
- [ ] Databases created (`sea-db`, `sea-redis`)
- [ ] Databases linked to apps
- [ ] Environment variables set
- [ ] Domain configured
- [ ] SSL enabled
- [ ] Deployed web: `git:from-image sea-web ghcr.io/mrailton/southeastarchers:latest`
- [ ] Deployed worker: `git:from-image sea-worker ghcr.io/mrailton/southeastarchers-worker:latest`
- [ ] Workers scaled: `ps:scale sea-worker worker=2`
- [ ] Migrations run: `run sea-web flask db upgrade`
- [ ] Admin created: `run sea-web python manage.py create-admin`
- [ ] GitHub Actions deploy automation configured (optional)

## Migration from Coolify

If you're currently on Coolify:

1. Export database from Coolify
2. Setup Dokku following this guide
3. Import database to Dokku MySQL
4. Deploy apps to Dokku
5. Update DNS to point to Dokku server
6. Test everything works
7. Decommission Coolify

## Resources

- Dokku Documentation: http://dokku.com/docs/
- Dokku GitHub: https://github.com/dokku/dokku
- MySQL Plugin: https://github.com/dokku/dokku-mysql
- Redis Plugin: https://github.com/dokku/dokku-redis
- Let's Encrypt Plugin: https://github.com/dokku/dokku-letsencrypt

## Support

For deployment issues:
1. Check `logs` command
2. Verify environment variables
3. Test database connection
4. Check Dokku documentation
5. Review server resources (disk, memory)
