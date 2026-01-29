#!/bin/bash
# Helix Deployment Script for apps01
# Usage: ./deploy.sh

set -e

DEPLOY_DIR="/home/apps01/helix"
PROJECT_NAME="helix"

echo "=== Helix Deployment ==="

# Navigate to deployment directory
cd "$DEPLOY_DIR"

# Pull latest changes (if git repo) or sync files
if [ -d ".git" ]; then
    echo "Pulling latest changes..."
    git pull origin main
fi

# Copy production env file
if [ -f "05_deployment/.env.production" ]; then
    echo "Setting up production environment..."
    cp 05_deployment/.env.production .env
fi

# Build and deploy with Docker Compose
echo "Building and starting services..."
docker compose down --remove-orphans 2>/dev/null || true
docker compose build --no-cache
docker compose up -d

# Wait for services to be healthy
echo "Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "=== Service Status ==="
docker compose ps

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: https://helix.aimagineers.io"
echo "API:      https://helix-api.aimagineers.io"
echo "API Docs: https://helix-api.aimagineers.io/docs"
