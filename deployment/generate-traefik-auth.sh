#!/bin/bash
# Generate Traefik dashboard credentials for .env file

echo "🔐 Traefik Dashboard Credentials Generator"
echo ""
echo "This will generate the TRAEFIK_DASHBOARD_CREDENTIALS value for your .env file"
echo ""

# Check if htpasswd is installed
if ! command -v htpasswd &> /dev/null; then
    echo "❌ htpasswd is not installed."
    echo ""
    echo "Install it:"
    echo "  Ubuntu/Debian: sudo apt-get install apache2-utils"
    echo "  CentOS/RHEL:   sudo yum install httpd-tools"
    echo "  macOS:         brew install httpd"
    exit 1
fi

# Prompt for username
read -p "Dashboard username (default: admin): " USERNAME
USERNAME=${USERNAME:-admin}

# Prompt for password
read -sp "Dashboard password: " PASSWORD
echo ""

if [ -z "$PASSWORD" ]; then
    echo "❌ Password cannot be empty"
    exit 1
fi

# Generate bcrypt hash
HASH=$(htpasswd -nbB "$USERNAME" "$PASSWORD")

# Escape dollar signs for .env file
ESCAPED_HASH=$(echo "$HASH" | sed -e 's/\$/\$\$/g')

echo ""
echo "✅ Generated credentials!"
echo ""
echo "Add this line to your deployment/.env file:"
echo ""
echo "TRAEFIK_DASHBOARD_CREDENTIALS=$ESCAPED_HASH"
echo ""
echo "Then you can access the dashboard at: https://traefik.${DOMAIN}"
echo "Login with: $USERNAME / [your password]"
