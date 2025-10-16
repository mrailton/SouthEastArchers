#!/bin/bash

# South East Archers - Start Script

echo "🏹 Starting South East Archers Web Application..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Check if database exists
if [ ! -f "instance/app.db" ]; then
    echo "⚠️  Database not found. Creating database..."
    flask db upgrade
    echo "✓ Database created"
    
    echo ""
    read -p "Would you like to create sample data? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python create_sample_data.py
    fi
fi

echo ""
echo "✓ Starting Flask development server..."
echo ""
echo "📍 Application will be available at: http://127.0.0.1:5000"
echo ""
echo "🔑 Default Login Credentials:"
echo "   Admin:  admin@southeastarchers.ie / admin123"
echo "   Member: member@example.com / member123"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start Flask
flask run
