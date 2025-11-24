#!/bin/bash
# Setup script for Docker Compose + Traefik deployment

set -e

echo "🚀 Setting up Docker Compose + Traefik deployment"
echo ""

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

# Copy .env.example if .env doesn't exist
if [ ! -f ../.env ]; then
    echo "📝 Creating .env file from example..."
    cp ../.env.example ../.env
    echo "⚠️  Please edit deployment/.env with your configuration"
    echo ""
fi

# Start Traefik
echo "🚀 Starting Traefik..."
docker compose up -d
echo "✅ Traefik is running"
echo ""

cd ..

# Setup South East Archers
echo "🏹 Setting up South East Archers application..."
cd southeastarchers

# Start application
echo "🚀 Starting South East Archers services..."
docker compose up -d
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
