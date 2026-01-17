#!/bin/bash

# Tunisia Parks Deployment Script
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-development}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

echo "🚀 Deploying Tunisia Parks to $ENVIRONMENT environment..."
echo "📄 Using compose file: $COMPOSE_FILE"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if .env file exists
ENV_FILE=".env"
if [ "$ENVIRONMENT" = "production" ]; then
    ENV_FILE=".env.production"
fi

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Error: $ENV_FILE file not found${NC}"
    exit 1
fi

echo -e "${BLUE}🔧 Using environment file: $ENV_FILE${NC}"

# Create necessary directories
echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
mkdir -p uploads/parks uploads/species uploads/users uploads/documents
mkdir -p ssl ssl-data

echo -e "${YELLOW}📦 Building Docker images...${NC}"
docker-compose -f $COMPOSE_FILE build --no-cache

echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose -f $COMPOSE_FILE up -d

echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 30

# Health check
echo -e "${YELLOW}🏥 Checking application health...${NC}"
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/health 2>/dev/null || echo "000")

if [ "$HEALTH_CHECK" -eq 200 ]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo -e "${GREEN}🌐 Application is running at: http://localhost:8002${NC}"
    echo -e "${GREEN}📚 API Documentation: http://localhost:8002/docs${NC}"

    if [ "$ENVIRONMENT" = "production" ]; then
        echo -e "${GREEN}🔒 Production deployment with SSL support${NC}"
    fi
else
    echo -e "${RED}❌ Deployment failed! Health check returned: $HEALTH_CHECK${NC}"
    echo -e "${YELLOW}📋 Checking logs...${NC}"
    docker-compose -f $COMPOSE_FILE logs app
    echo -e "${YELLOW}🔄 Trying to restart services...${NC}"
    docker-compose -f $COMPOSE_FILE restart app
    sleep 10

    # Second health check
    HEALTH_CHECK2=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/health 2>/dev/null || echo "000")
    if [ "$HEALTH_CHECK2" -eq 200 ]; then
        echo -e "${GREEN}✅ Services recovered after restart!${NC}"
    else
        echo -e "${RED}❌ Services still failing. Manual intervention required.${NC}"
        exit 1
    fi
fi

# Show running containers
echo -e "${YELLOW}📊 Running containers:${NC}"
docker-compose -f $COMPOSE_FILE ps

# Show resource usage
echo -e "${YELLOW}💾 Resource usage:${NC}"
docker-compose -f $COMPOSE_FILE exec -T app python -c "
import psutil
import os
print(f'CPU Usage: {psutil.cpu_percent()}%')
print(f'Memory Usage: {psutil.virtual_memory().percent}%')
print(f'Disk Usage: {psutil.disk_usage(\"/\").percent}%')
" 2>/dev/null || echo "Resource monitoring not available"

echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo -e "${BLUE}💡 Useful commands:${NC}"
echo -e "   • View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo -e "   • Stop services: docker-compose -f $COMPOSE_FILE down"
echo -e "   • Monitor: ./monitor.sh"
echo -e "   • Backup DB: cp tunisia_parks.db tunisia_parks.db.backup"
# ---------- END OF FILE ----------
