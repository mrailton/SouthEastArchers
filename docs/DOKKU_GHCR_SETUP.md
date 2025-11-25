# Dokku Deployment with GHCR Images - Quick Start

This guide shows how to deploy your existing GHCR Docker images to Dokku.

## Prerequisites

✅ GitHub Actions already building and pushing images to GHCR:
- `ghcr.io/mrailton/southeastarchers:latest`
- `ghcr.io/mrailton/southeastarchers-worker:latest`

## Step-by-Step Setup

### 1. Install Dokku on Server

```bash
# SSH into your server
ssh root@your-server

# Install Dokku
wget -NP . https://dokku.com/install/v0.35.11/bootstrap.sh
sudo DOKKU_TAG=v0.35.11 bash bootstrap.sh

# Install plugins
sudo dokku plugin:install https://github.com/dokku/dokku-mysql.git mysql
sudo dokku plugin:install https://github.com/dokku/dokku-redis.git redis
sudo dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git
```

### 2. Login to GHCR

```bash
# Still on server as root
docker login ghcr.io -u mrailton -p YOUR_GITHUB_PAT
```

> **Get a PAT**: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
> Required permission: `read:packages`

### 3. Create Apps

```bash
# Create applications
dokku apps:create sea-web
dokku apps:create sea-worker

# Configure to use Docker images (not buildpacks)
dokku builder:set sea-web selected docker-image
dokku builder:set sea-worker selected docker-image
```

### 4. Create and Link Databases

```bash
# Create databases
dokku mysql:create sea-db
dokku redis:create sea-redis

# Link to apps (auto-sets DATABASE_URL and REDIS_URL)
dokku mysql:link sea-db sea-web
dokku mysql:link sea-db sea-worker
dokku redis:link sea-redis sea-web
dokku redis:link sea-redis sea-worker
```

### 5. Configure Environment Variables

```bash
# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)

# Web app config
dokku config:set sea-web \
  FLASK_ENV=production \
  SECRET_KEY=$SECRET_KEY \
  MAIL_SERVER=smtp.gmail.com \
  MAIL_PORT=587 \
  MAIL_USE_TLS=True \
  MAIL_USERNAME=your@gmail.com \
  MAIL_PASSWORD=your-app-password \
  MAIL_DEFAULT_SENDER=noreply@southeastarchers.ie \
  SUMUP_API_KEY=your-key \
  SUMUP_MERCHANT_CODE=your-code

# Worker config (same SECRET_KEY)
dokku config:set sea-worker \
  FLASK_ENV=production \
  SECRET_KEY=$SECRET_KEY \
  MAIL_SERVER=smtp.gmail.com \
  MAIL_PORT=587 \
  MAIL_USE_TLS=True \
  MAIL_USERNAME=your@gmail.com \
  MAIL_PASSWORD=your-app-password \
  MAIL_DEFAULT_SENDER=noreply@southeastarchers.ie
```

### 6. Setup Domain and SSL

```bash
# Add domain
dokku domains:add sea-web southeastarchers.ie
dokku domains:add sea-web www.southeastarchers.ie

# Enable Let's Encrypt SSL
dokku letsencrypt:enable sea-web

# Auto-renew certificates
dokku letsencrypt:cron-job --add sea-web
```

### 7. Deploy from GHCR

```bash
# Deploy web application
dokku git:from-image sea-web ghcr.io/mrailton/southeastarchers:latest

# Deploy worker application
dokku git:from-image sea-worker ghcr.io/mrailton/southeastarchers-worker:latest

# Scale workers to 2 instances
dokku ps:scale sea-worker worker=2
```

### 8. Run Database Migrations

```bash
# Run migrations
dokku run sea-web flask db upgrade

# Create admin user
dokku run sea-web python manage.py create-admin
```

### 9. Verify Deployment

```bash
# Check status
dokku apps:info sea-web
dokku ps:report sea-web

# View logs
dokku logs sea-web -t
dokku logs sea-worker -t
```

## Automatic Deployment from GitHub Actions

### Option 1: SSH-Based Deploy (Recommended)

Add secrets to GitHub repo:
- `DOKKU_HOST` - Your server IP or domain
- `DOKKU_SSH_KEY` - Private SSH key for dokku user

The workflow file `.github/workflows/deploy-dokku.yml` is already created and will:
1. Wait for CI workflow to complete
2. SSH into Dokku server
3. Pull latest images from GHCR
4. Deploy both web and worker apps
5. Ensure workers are scaled properly

### Option 2: Manual Deploy

After GitHub Actions pushes new images:

```bash
# SSH into server and deploy
ssh dokku@your-server git:from-image sea-web ghcr.io/mrailton/southeastarchers:latest
ssh dokku@your-server git:from-image sea-worker ghcr.io/mrailton/southeastarchers-worker:latest
```

## Daily Operations

### Update Application

Just push to main branch:
```bash
git push origin main
```

GitHub Actions will:
1. Build new images
2. Push to GHCR
3. Trigger Dokku deployment (if workflow configured)

Or manually:
```bash
ssh dokku@your-server git:from-image sea-web ghcr.io/mrailton/southeastarchers:latest
ssh dokku@your-server git:from-image sea-worker ghcr.io/mrailton/southeastarchers-worker:latest
```

### View Logs

```bash
ssh dokku@your-server logs sea-web -t
ssh dokku@your-server logs sea-worker -t
```

### Scale Workers

```bash
ssh dokku@your-server ps:scale sea-worker worker=3
```

### Run Commands

```bash
# Run migrations
ssh dokku@your-server run sea-web flask db upgrade

# Django-style manage commands
ssh dokku@your-server run sea-web python manage.py your-command

# Access Flask shell
ssh dokku@your-server run sea-web flask shell
```

### Database Backup

```bash
# Export
ssh dokku@your-server mysql:export sea-db > backup-$(date +%Y%m%d).sql

# Import
ssh dokku@your-server mysql:import sea-db < backup.sql
```

### Environment Variables

```bash
# View all config
ssh dokku@your-server config:show sea-web

# Add/update variable
ssh dokku@your-server config:set sea-web NEW_VAR=value

# Remove variable
ssh dokku@your-server config:unset sea-web OLD_VAR
```

## Troubleshooting

### Image Pull Fails

```bash
# Re-login to GHCR
docker login ghcr.io -u mrailton -p YOUR_PAT

# Verify you can pull
docker pull ghcr.io/mrailton/southeastarchers:latest
```

### App Won't Start

```bash
# Check logs
dokku logs sea-web -t

# Check config
dokku config:show sea-web

# Verify DATABASE_URL is set
dokku config:get sea-web DATABASE_URL

# Check processes
dokku ps:report sea-web
```

### Worker Not Processing Jobs

```bash
# Check worker logs
dokku logs sea-worker -t

# Check scaling
dokku ps:report sea-worker

# Restart workers
dokku ps:restart sea-worker
```

### SSL Issues

```bash
# Re-enable Let's Encrypt
dokku letsencrypt:enable sea-web

# Check certificate
dokku letsencrypt:list
```

## Advantages Over Other Solutions

### vs Coolify
- **Simpler**: No web UI overhead, just CLI
- **Faster**: No builder, uses your existing images
- **Lighter**: Lower memory footprint
- **More Control**: Direct Docker/Linux access

### vs Docker Compose + Traefik
- **Zero-downtime deploys**: Built-in
- **SSL management**: Automatic via Let's Encrypt
- **Easier scaling**: `ps:scale` command
- **Built-in health checks**: Automatic rollback on failure
- **Database management**: Plugins handle everything

### vs Heroku
- **Cost**: Free (just server costs)
- **Control**: Full server access
- **No limits**: No dyno hours, build minutes, etc.
- **Same workflow**: Git-based deployment

## Cost Estimate

**Monthly Server Costs:**
- 2GB VPS: $10-15/month (Hetzner, DigitalOcean, Linode)
- 4GB VPS: $20-25/month (recommended for production)

**vs Heroku:**
- Heroku Eco (2 dynos): $10/month
- Professional: $50/month minimum
- Add-ons: $15-100/month (database, redis, etc.)

**Dokku saves $40-100+/month** for typical Flask app with worker.

## Next Steps

1. ✅ Complete setup steps above
2. Test deployment end-to-end
3. Configure GitHub Actions auto-deploy
4. Set up monitoring (optional)
5. Configure backups (recommended)

## Resources

- Dokku Docs: http://dokku.com/docs/
- MySQL Plugin: https://github.com/dokku/dokku-mysql
- Redis Plugin: https://github.com/dokku/dokku-redis
- Let's Encrypt Plugin: https://github.com/dokku/dokku-letsencrypt
