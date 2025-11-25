#!/bin/bash
# Quick setup script for Dokku deployment

SERVER="$1"

if [ -z "$SERVER" ]; then
    echo "Usage: ./setup-dokku.sh user@your-server"
    exit 1
fi

echo "🚀 Setting up Dokku deployment on $SERVER"
echo ""

echo "📋 Run these commands on your server:"
echo ""

echo "# 0. Login to GHCR"
echo "docker login ghcr.io -u YOUR_GITHUB_USERNAME -p YOUR_GITHUB_PAT"
echo ""

echo "# 1. Create apps"
echo "dokku apps:create sea-web"
echo "dokku apps:create sea-worker"
echo ""

echo "# 2. Configure to use Docker images from GHCR"
echo "dokku builder:set sea-web selected docker-image"
echo "dokku builder:set sea-worker selected docker-image"
echo ""
echo "# 3. Create databases"
echo "dokku mysql:create sea-db"
echo "dokku redis:create sea-redis"
echo ""
echo "# 4. Link databases"
echo "dokku mysql:link sea-db sea-web"
echo "dokku mysql:link sea-db sea-worker"
echo "dokku redis:link sea-redis sea-web"
echo "dokku redis:link sea-redis sea-worker"
echo ""
echo "# 5. Set environment variables"
echo "dokku config:set sea-web FLASK_ENV=production SECRET_KEY=\$(openssl rand -hex 32) MAIL_SERVER=smtp.gmail.com ..."
echo "dokku config:set sea-worker FLASK_ENV=production SECRET_KEY=\$(openssl rand -hex 32) ..."
echo ""
echo "# 6. Setup domain and SSL"
echo "dokku domains:add sea-web southeastarchers.ie"
echo "dokku letsencrypt:enable sea-web"
echo ""
echo "# 7. Deploy from GHCR images!"
echo "dokku git:from-image sea-web ghcr.io/mrailton/southeastarchers:latest"
echo "dokku git:from-image sea-worker ghcr.io/mrailton/southeastarchers-worker:latest"
echo ""
echo "# 8. Scale workers"
echo "dokku ps:scale sea-worker worker=2"
echo ""
echo "# 9. Run migrations"
echo "dokku run sea-web flask db upgrade"
echo "dokku run sea-web python manage.py create-admin"
echo ""
echo "📚 Full guide: docs/DOKKU_DEPLOYMENT.md"
