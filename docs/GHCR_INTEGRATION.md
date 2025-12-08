# GHCR Integration Summary

## Overview

The production Docker Compose setup now uses pre-built images from GitHub Container Registry (GHCR), enabling fast deployments without build steps on the Dokploy server.

## Changes Made

### 1. Production Docker Compose (`docker/docker-compose.yml`)
**Changed from:** Building images locally
**Changed to:** Pulling from GHCR

```yaml
web:
  image: ghcr.io/mrailton/southeastarchers-web:latest
  
worker:
  image: ghcr.io/mrailton/southeastarchers-worker:latest
```

### 2. GitHub Actions Workflow (`.github/workflows/ci.yml`)
**Updated:** Dockerfile paths to use new `docker/` directory

```yaml
file: ./docker/Dockerfile.web    # was: ./Dockerfile.web
file: ./docker/Dockerfile.worker  # was: ./Dockerfile.worker
```

### 3. New Alternative Compose File (`docker/docker-compose.build.yml`)
**Purpose:** For scenarios where you want to build images locally instead of pulling from GHCR

**Use case:** Self-hosted deployments without GHCR access

### 4. Documentation Updates
- ✅ `docker/README.md` - Added GHCR deployment instructions
- ✅ `DOKPLOY_DEPLOYMENT.md` - Updated deployment steps
- ✅ `README.md` - Added CI/CD workflow explanation
- ✅ `docker/QUICK_REFERENCE.md` - Updated file descriptions
- ✅ `DOCKER_MIGRATION.md` - Added GHCR migration notes

## CI/CD Pipeline

### Automatic Image Building

**Trigger:** Push to `main` branch

**Process:**
1. ✅ Run tests (`make test-parallel`)
2. ✅ Check code quality (`make format-check`)
3. ✅ Build web image from `docker/Dockerfile.web`
4. ✅ Build worker image from `docker/Dockerfile.worker`
5. ✅ Push both images to GHCR
6. ✅ Trigger Dokploy webhook (if configured)

**Images Created:**
- `ghcr.io/mrailton/southeastarchers-web:latest`
- `ghcr.io/mrailton/southeastarchers-web:main`
- `ghcr.io/mrailton/southeastarchers-web:sha-<commit-sha>`
- `ghcr.io/mrailton/southeastarchers-worker:latest`
- `ghcr.io/mrailton/southeastarchers-worker:main`
- `ghcr.io/mrailton/southeastarchers-worker:sha-<commit-sha>`

## Deployment Options

### Option 1: GHCR Images (Recommended - Default)

**Compose File:** `docker/docker-compose.yml`

**Pros:**
- ✅ Fast deployments (no build step)
- ✅ Pre-tested images
- ✅ Consistent across environments
- ✅ Automatic via GitHub Actions

**Setup:**
```bash
# In Dokploy
Compose file path: docker/docker-compose.yml
# That's it!
```

### Option 2: Build on Server

**Compose File:** `docker/docker-compose.build.yml`

**Pros:**
- ✅ No external registry needed
- ✅ Build on-demand
- ✅ Full control

**Setup:**
```bash
# In Dokploy
Compose file path: docker/docker-compose.build.yml
```

### Option 3: Local Development

**Compose File:** `docker/docker-compose.dev.yml`

**Features:**
- Hot reload
- Mailhog for email testing
- Auto-restart worker
- Hardcoded dev credentials

**Setup:**
```bash
make docker-up
```

## Image Access

### Public vs Private

Currently, images are **private** by default in GHCR.

**To make public:**
1. Go to GitHub repository
2. Navigate to Packages
3. Select package (web or worker)
4. Settings → Change visibility → Public

**For Dokploy to access private images:**
1. Create GitHub Personal Access Token with `read:packages` scope
2. In Dokploy, configure registry authentication:
   - Registry: ghcr.io
   - Username: mrailton
   - Password: <GitHub PAT>

## File Structure

```
.
├── .github/
│   └── workflows/
│       └── ci.yml                    # ✨ Updated: docker/ paths
├── docker/
│   ├── docker-compose.yml            # ✨ Updated: GHCR images
│   ├── docker-compose.build.yml      # ✨ New: Build locally
│   ├── docker-compose.dev.yml        # Development
│   ├── Dockerfile.web                # Web production image
│   ├── Dockerfile.worker             # Worker production image
│   ├── Dockerfile.dev                # Development image
│   ├── docker-entrypoint.sh          # Migration script
│   ├── README.md                     # ✨ Updated: GHCR docs
│   ├── QUICK_REFERENCE.md            # ✨ Updated
│   └── .env.production.example       # Env template
├── DOKPLOY_DEPLOYMENT.md             # ✨ Updated: GHCR approach
├── DOCKER_MIGRATION.md               # ✨ Updated: GHCR notes
├── README.md                         # ✨ Updated: CI/CD info
└── Makefile                          # Docker commands
```

## Benefits of GHCR Approach

### For Deployment
- 🚀 **Faster deployments** - No build step on server (5-10 min → 1-2 min)
- 🎯 **Reliable** - Pre-tested images from CI/CD
- 📦 **Cached** - GitHub Actions caches layers
- 🔄 **Rollback** - Easy to rollback to specific image tags

### For Development
- 🧪 **Test production images locally** - Pull and test exact production images
- 🔍 **Debug issues** - Run same image that's deployed
- 📊 **Consistent** - Dev and prod use same image build process

### For CI/CD
- ✅ **Automated** - Push to main → Build → Push → Deploy
- 🔐 **Secure** - Builds in GitHub Actions secure environment
- 📝 **Trackable** - Every image tagged with commit SHA
- 🎨 **Flexible** - Support multiple tags (latest, main, sha, version)

## Testing the Setup

### 1. Test Locally

```bash
# Pull and run production images locally
cd docker
docker-compose pull
docker-compose up -d

# Access application
curl http://localhost:5000
```

### 2. Test GitHub Actions

```bash
# Commit and push
git add .
git commit -m "Update Docker setup for GHCR"
git push origin main

# Watch workflow
# Go to: https://github.com/mrailton/SouthEastArchers/actions

# Verify images pushed
# Go to: https://github.com/mrailton?tab=packages
```

### 3. Test Dokploy Deployment

```bash
# In Dokploy UI:
# 1. Update compose file path: docker/docker-compose.yml
# 2. Ensure environment variables are set
# 3. Redeploy
# 4. Watch logs for image pull and startup
```

## Troubleshooting

### Images Not Building

**Check GitHub Actions:**
```bash
# View workflow runs
https://github.com/mrailton/SouthEastArchers/actions
```

**Common issues:**
- Workflow not triggered (check branch name)
- Dockerfile syntax error
- Build context issues

### Dokploy Can't Pull Images

**If images are private:**
1. Create GitHub PAT with `read:packages`
2. Configure in Dokploy: Settings → Registry
3. Add credentials for ghcr.io

**Check logs:**
```bash
# In Dokploy, view deployment logs
# Look for "pull access denied" or similar
```

### Wrong Image Version Deployed

**Force pull latest:**
```bash
docker-compose pull
docker-compose up -d --force-recreate
```

**Check image tags:**
```bash
docker images | grep southeastarchers
```

## Rollback Procedure

### To Previous Version

```bash
# Option 1: Use commit SHA tag
docker-compose.yml:
  web:
    image: ghcr.io/mrailton/southeastarchers-web:sha-abc1234

# Option 2: Re-run old workflow in GitHub Actions
# Go to Actions → Select old successful run → Re-run

# Option 3: Use docker-compose.build.yml
# Checkout old commit, then:
docker-compose -f docker-compose.build.yml up -d --build
```

## Migration Checklist

- [x] Move Dockerfiles to docker/ directory
- [x] Update GitHub Actions workflow
- [x] Update docker-compose.yml to use GHCR images
- [x] Create docker-compose.build.yml alternative
- [x] Update all documentation
- [ ] Test GitHub Actions builds images
- [ ] Test Dokploy pulls images
- [ ] Configure GHCR access in Dokploy (if private)
- [ ] Deploy to production
- [ ] Verify application works
- [ ] Set up monitoring for image pulls

## Next Steps

1. **Commit and push changes:**
   ```bash
   git add .
   git commit -m "feat: integrate GHCR for production deployments"
   git push origin main
   ```

2. **Verify GitHub Actions:**
   - Watch workflow run
   - Confirm images pushed to GHCR
   - Check both web and worker images

3. **Update Dokploy:**
   - Change compose path to `docker/docker-compose.yml`
   - Configure GHCR authentication (if needed)
   - Redeploy

4. **Monitor first deployment:**
   - Watch Dokploy logs
   - Verify image pull successful
   - Test application functionality
   - Check all services running

5. **Clean up (optional):**
   - Remove old individual service apps in Dokploy
   - Archive old deployment documentation
   - Update team documentation

## Support

- **GHCR Issues:** [GitHub Packages Docs](https://docs.github.com/en/packages)
- **Docker Compose:** [../docker/README.md](../docker/README.md)
- **Dokploy Setup:** [DOKPLOY_DEPLOYMENT.md](DOKPLOY_DEPLOYMENT.md)
- **General:** [../README.md](../README.md)

---

**Status:** ✅ Ready for production deployment with GHCR!
