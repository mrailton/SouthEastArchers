#!/bin/bash
# Login to GitHub Container Registry

echo "🔐 Logging into GitHub Container Registry (GHCR)..."
echo ""
echo "You'll need a GitHub Personal Access Token with 'read:packages' permission"
echo ""
echo "To create one:"
echo "  1. Go to: https://github.com/settings/tokens/new"
echo "  2. Name: 'GHCR Pull Token'"
echo "  3. Select scope: 'read:packages'"
echo "  4. Click 'Generate token'"
echo "  5. Copy the token"
echo ""

read -p "GitHub Username: " GITHUB_USERNAME
read -sp "GitHub Token (PAT): " GITHUB_TOKEN
echo ""

# Login to GHCR
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USERNAME" --password-stdin

if [ $? -eq 0 ]; then
    echo "✅ Successfully logged into GHCR"
    echo ""
    echo "Now you can run: ./setup.sh"
else
    echo "❌ Login failed. Please check your credentials."
    exit 1
fi
