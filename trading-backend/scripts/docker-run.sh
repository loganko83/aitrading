#!/bin/bash

# TradingBot AI - Docker Run Script
# Manages docker-compose operations

set -e

echo "=========================================="
echo "TradingBot AI - Docker Management"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env.docker"

# Check if docker-compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "${RED}❌ Error: $COMPOSE_FILE not found!${NC}"
    exit 1
fi

# Check if .env.docker exists
if [ ! -f "$ENV_FILE" ]; then
    echo "${YELLOW}⚠️  Warning: $ENV_FILE not found!${NC}"
    echo "Creating from template..."
    if [ -f ".env.docker.example" ]; then
        cp .env.docker.example .env.docker
        echo "${GREEN}✅ Created .env.docker from template${NC}"
        echo "${YELLOW}⚠️  Please edit .env.docker with your credentials before running!${NC}"
        exit 1
    else
        echo "${RED}❌ No template found. Please create .env.docker manually.${NC}"
        exit 1
    fi
fi

# Function to show usage
usage() {
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  up          Start all services (detached mode)"
    echo "  down        Stop all services"
    echo "  restart     Restart all services"
    echo "  logs        Show logs (follow mode)"
    echo "  ps          Show running containers"
    echo "  build       Rebuild all images"
    echo "  clean       Stop and remove all containers, networks, and volumes"
    echo "  health      Check health of all services"
    echo ""
    echo "Options:"
    echo "  --prod      Use production profile (includes Nginx)"
    echo ""
}

# Parse options
PROFILE_FLAG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --prod)
            PROFILE_FLAG="--profile production"
            shift
            ;;
        up|down|restart|logs|ps|build|clean|health)
            COMMAND=$1
            shift
            ;;
        *)
            echo "${RED}❌ Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Execute command
case $COMMAND in
    up)
        echo "${YELLOW}🚀 Starting TradingBot AI services...${NC}"
        docker-compose $PROFILE_FLAG up -d
        echo ""
        echo "${GREEN}✅ Services started!${NC}"
        echo ""
        echo "View logs: $0 logs"
        echo "Check health: $0 health"
        echo "API: http://localhost:8001/docs"
        ;;

    down)
        echo "${YELLOW}🛑 Stopping TradingBot AI services...${NC}"
        docker-compose $PROFILE_FLAG down
        echo "${GREEN}✅ Services stopped!${NC}"
        ;;

    restart)
        echo "${YELLOW}🔄 Restarting TradingBot AI services...${NC}"
        docker-compose $PROFILE_FLAG restart
        echo "${GREEN}✅ Services restarted!${NC}"
        ;;

    logs)
        echo "${YELLOW}📋 Showing logs (Ctrl+C to exit)...${NC}"
        docker-compose $PROFILE_FLAG logs -f
        ;;

    ps)
        echo "${YELLOW}📊 Running containers:${NC}"
        docker-compose $PROFILE_FLAG ps
        ;;

    build)
        echo "${YELLOW}🔨 Building all images...${NC}"
        docker-compose $PROFILE_FLAG build --no-cache
        echo "${GREEN}✅ Build complete!${NC}"
        ;;

    clean)
        echo "${RED}⚠️  This will remove all containers, networks, and volumes!${NC}"
        read -p "Are you sure? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "${YELLOW}🧹 Cleaning up...${NC}"
            docker-compose $PROFILE_FLAG down -v --remove-orphans
            echo "${GREEN}✅ Cleanup complete!${NC}"
        else
            echo "Cancelled."
        fi
        ;;

    health)
        echo "${YELLOW}🏥 Checking service health...${NC}"
        echo ""

        # Check PostgreSQL
        echo -n "PostgreSQL: "
        if docker-compose exec -T postgres pg_isready -U tradingbot > /dev/null 2>&1; then
            echo "${GREEN}✅ Healthy${NC}"
        else
            echo "${RED}❌ Unhealthy${NC}"
        fi

        # Check Redis
        echo -n "Redis:      "
        if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            echo "${GREEN}✅ Healthy${NC}"
        else
            echo "${RED}❌ Unhealthy${NC}"
        fi

        # Check Backend
        echo -n "Backend:    "
        if curl -sf http://localhost:8001/api/v1/health > /dev/null 2>&1; then
            echo "${GREEN}✅ Healthy${NC}"
        else
            echo "${RED}❌ Unhealthy${NC}"
        fi

        echo ""
        ;;

    *)
        usage
        exit 1
        ;;
esac

echo "=========================================="
