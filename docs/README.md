# Documentation Index

Welcome to the South East Archers documentation!

## 📚 Getting Started

- [Main README](../README.md) - Project overview and quick start

## 🐳 Docker & Deployment

- [Docker Setup Guide](../docker/README.md) - Comprehensive Docker Compose documentation
- [Docker Quick Reference](../docker/QUICK_REFERENCE.md) - Quick command reference
- [Dokploy Deployment Guide](DOKPLOY_DEPLOYMENT.md) - Step-by-step deployment to Dokploy
- [GHCR Integration Guide](GHCR_INTEGRATION.md) - Using GitHub Container Registry
- [Docker Migration Notes](DOCKER_MIGRATION.md) - What changed in the Docker setup

## 🔧 Technical Guides

- [Background Jobs Guide](BACKGROUND_JOBS.md) - Redis & RQ setup (if exists)
- [RQ Worker Context Fix](RQ_WORKER_FIX.md) - Flask application context in workers
- [Sum Up Warning Fix](SUMUP_WARNING_FIX.md) - Third-party library warning suppression

## 📦 Legacy Documentation

- [Coolify Deployment](COOLIFY_DEPLOYMENT.md) - Legacy deployment guide (if exists)

## 🗂️ Documentation Structure

```
.
├── README.md                       # Main project documentation
├── docs/
│   ├── README.md                   # This file - documentation index
│   ├── DOKPLOY_DEPLOYMENT.md       # Dokploy deployment guide
│   ├── GHCR_INTEGRATION.md         # GHCR integration guide
│   ├── DOCKER_MIGRATION.md         # Docker migration notes
│   ├── SUMUP_WARNING_FIX.md        # Third-party warning fix
│   └── BACKGROUND_JOBS.md          # Background jobs guide
└── docker/
    ├── README.md                   # Docker Compose guide
    └── QUICK_REFERENCE.md          # Docker quick reference
```

## 🔍 Quick Links

### For New Developers
1. Start with [Main README](../README.md)
2. Set up development: [Docker Setup Guide](../docker/README.md)
3. Use quick reference: [Docker Quick Reference](../docker/QUICK_REFERENCE.md)

### For Deployment
1. Follow: [Dokploy Deployment Guide](DOKPLOY_DEPLOYMENT.md)
2. Understand CI/CD: [GHCR Integration Guide](GHCR_INTEGRATION.md)
3. Troubleshoot: [Docker Migration Notes](DOCKER_MIGRATION.md)

### For Operations
1. Check: [Docker Quick Reference](../docker/QUICK_REFERENCE.md)
2. Background jobs: [Background Jobs Guide](BACKGROUND_JOBS.md)
3. Issues: [Sum Up Warning Fix](SUMUP_WARNING_FIX.md)

## 💡 Need Help?

- Check the relevant guide above
- Review the [Main README](../README.md)
- Open an issue on GitHub

---

**Last Updated:** December 2024
