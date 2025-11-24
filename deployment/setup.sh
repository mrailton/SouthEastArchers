#!/bin/bash
# Setup script for Docker Compose + Traefik deployment

set -e

echo "🚀 Setting up Docker Compose + Traefik deployment"
echo ""

# Check if logged into GHCR
if ! docker login ghcr.io --password-stdin < /dev/null 2>&1 | grep -q "Login Succeeded"; then
    if [ ! -f ~/.docker/config.json ] || ! grep -q "ghcr.io" ~/.docker/config.json; then
        echo "❌ Not logged into GitHub Container Registry (GHCR)"
        echo ""
        echo "Run this first: ./login-ghcr.sh"
        echo ""
        exit 1
    fi
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create traefik network
echo "📡 Creating traefik network..."
docker network create traefik 2>/dev/null || echo "Network 'traefik' already exists"
echo ""

# Setup Traefik directory
echo "🔧 Setting up Traefik..."
cd traefik

# Create acme.json with correct permissions
touch acme.json
chmod 600 acme.json
echo "✅ Created acme.json for SSL certificates"

# Check if .env exists
if [ ! -f .env ]; then
    if [ -f ../.env ]; then
        echo "📝 Copying .env to traefik directory..."
        cp ../.env .env
    else
        echo "❌ .env file not found! Please create deployment/.env first"
        echo "   Example: cp deployment/.env.example deployment/.env"
        exit 1
    fi
fi

# Start Traefik
echo "🚀 Starting Traefik..."
docker compose --env-file .env up -d
echo "✅ Traefik is running"
echo ""

cd ..

# Setup South East Archers
echo "🏹 Setting up South East Archers application..."
cd southeastarchers

# Check if .env exists
if [ ! -f .env ]; then
    if [ -f ../.env ]; then
        echo "📝 Copying .env to southeastarchers directory..."
        cp ../.env .env
    else
        echo "❌ .env file not found! Please create deployment/.env first"
        exit 1
    fi
fi

# Start application
echo "🚀 Starting South East Archers services..."
docker compose --env-file .env up -d
echo "✅ Application services are running"
echo ""

cd ../..

echo "✨ Setup complete!"
echo ""
echo "📊 Service Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "🌐 Access Points:"
echo "  - Application: https://southeastarchers.ie"
echo "  - Traefik Dashboard: https://traefik.${DOMAIN:-yourdomain.com}"
echo ""
echo "📝 Next Steps:"
echo "  1. Edit deployment/.env with your actual configuration"
echo "  2. Run database migrations: docker exec sea-web flask db upgrade"
echo "  3. Create admin user: docker exec -it sea-web python manage.py create-admin"
echo ""
echo "🔍 Useful Commands:"
echo "  - View logs: docker compose -f deployment/southeastarchers/docker-compose.yml logs -f"
echo "  - Restart services: docker compose -f deployment/southeastarchers/docker-compose.yml restart"
echo "  - Update images: docker compose -f deployment/southeastarchers/docker-compose.yml pull"
echo "  - Scale workers: docker compose -f deployment/southeastarchers/docker-compose.yml up -d --scale worker=3"
