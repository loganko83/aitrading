#!/bin/bash

# TradingBot AI - Docker Build Script
# Builds the Docker image for production

set -e

echo "=========================================="
echo "TradingBot AI - Docker Build"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="tradingbot-backend"
TAG="${1:-latest}"
DOCKERFILE="Dockerfile"

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE" ]; then
    echo "❌ Error: $DOCKERFILE not found!"
    exit 1
fi

# Build the image
echo ""
echo "${YELLOW}🔨 Building Docker image...${NC}"
echo "Image: $IMAGE_NAME:$TAG"
echo ""

docker build \
    --tag "$IMAGE_NAME:$TAG" \
    --file "$DOCKERFILE" \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
    --progress=plain \
    .

# Check build result
if [ $? -eq 0 ]; then
    echo ""
    echo "${GREEN}✅ Docker image built successfully!${NC}"
    echo ""
    echo "Image details:"
    docker images "$IMAGE_NAME:$TAG"
    echo ""
    echo "To run the image:"
    echo "  docker-compose up -d"
    echo ""
else
    echo ""
    echo "❌ Docker build failed!"
    exit 1
fi

# Optional: Tag as latest
if [ "$TAG" != "latest" ]; then
    read -p "Tag as 'latest' as well? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker tag "$IMAGE_NAME:$TAG" "$IMAGE_NAME:latest"
        echo "${GREEN}✅ Tagged as latest${NC}"
    fi
fi

# Show image size
echo ""
echo "Image size:"
docker images "$IMAGE_NAME:$TAG" --format "{{.Repository}}:{{.Tag}} - {{.Size}}"
echo ""

echo "=========================================="
echo "✅ Build complete!"
echo "=========================================="
