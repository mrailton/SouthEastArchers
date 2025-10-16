#!/bin/bash
# Quick start script for Docker deployment

set -e

echo "🏹 South East Archers - Docker Deployment"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your configuration."
    echo ""
fi

# Parse command line arguments
COMMAND=${1:-up}

case "$COMMAND" in
    "up"|"start")
        echo "🚀 Starting application..."
        docker-compose up -d
        echo ""
        echo "✅ Application started!"
        echo "   URL: http://localhost:5000"
        echo ""
        echo "Run migrations with: ./scripts/docker-run.sh migrate"
        ;;
    
    "down"|"stop")
        echo "🛑 Stopping application..."
        docker-compose down
        echo "✅ Application stopped!"
        ;;
    
    "restart")
        echo "🔄 Restarting application..."
        docker-compose restart
        echo "✅ Application restarted!"
        ;;
    
    "logs")
        echo "📜 Viewing logs (Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
    
    "migrate")
        echo "🗄️  Running database migrations..."
        docker-compose exec web flask db upgrade
        echo "✅ Migrations complete!"
        ;;
    
    "sample-data")
        echo "📊 Creating sample data..."
        docker-compose exec web python create_sample_data.py
        echo "✅ Sample data created!"
        ;;
    
    "shell")
        echo "🐚 Opening shell in container..."
        docker-compose exec web sh
        ;;
    
    "build")
        echo "🔨 Building Docker image..."
        docker-compose build
        echo "✅ Build complete!"
        ;;
    
    "pull")
        echo "📥 Pulling latest image from GHCR..."
        docker-compose pull
        echo "✅ Pull complete!"
        ;;
    
    "clean")
        echo "🧹 Cleaning up..."
        docker-compose down -v
        echo "✅ Cleanup complete!"
        ;;
    
    "status")
        echo "📊 Container status:"
        docker-compose ps
        ;;
    
    "help"|"-h"|"--help")
        echo "Usage: ./scripts/docker-run.sh [command]"
        echo ""
        echo "Commands:"
        echo "  up, start      Start the application"
        echo "  down, stop     Stop the application"
        echo "  restart        Restart the application"
        echo "  logs           View logs"
        echo "  migrate        Run database migrations"
        echo "  sample-data    Create sample data"
        echo "  shell          Open shell in container"
        echo "  build          Build Docker image"
        echo "  pull           Pull latest image from GHCR"
        echo "  clean          Stop and remove all containers and volumes"
        echo "  status         Show container status"
        echo "  help           Show this help message"
        ;;
    
    *)
        echo "❌ Unknown command: $COMMAND"
        echo "Run './scripts/docker-run.sh help' for usage information"
        exit 1
        ;;
esac
