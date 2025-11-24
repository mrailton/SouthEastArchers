#!/bin/bash
# Quick fix for deployment setup

echo "🔧 Fixing deployment configuration..."

# Ensure .env is in the deployment directory
if [ ! -f deployment/.env ]; then
    echo "❌ Please create deployment/.env file first!"
    echo ""
    echo "Example:"
    echo "  cd deployment"
    echo "  cp .env.example .env"
    echo "  nano .env  # Edit with your values"
    exit 1
fi

# Copy .env to subdirectories
echo "📝 Copying .env to service directories..."
cp deployment/.env deployment/traefik/.env
cp deployment/.env deployment/southeastarchers/.env
echo "✅ .env files copied"

echo ""
echo "✨ Now you can run: cd deployment && ./setup.sh"
