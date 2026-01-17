#!/bin/bash

# Tunisia Parks Deployment Script
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}

echo "🚀 Deploying Tunisia Parks to $ENVIRONMENT environment..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if .env file exists
if [ ! -f ".env.$ENVIRONMENT" ]; then
    echo -e "${RED}❌ Error: .env.$ENVIRONMENT file not found${NC}"
    exit 1
fi

# Load environment variables
export $(cat .env.$ENVIRONMENT | grep -v '^#' | xargs)

echo -e "${YELLOW}📦 Building Docker images...${NC}"
docker-compose build --no-cache

echo -e "${YELLOW}🗄️  Setting up database...${NC}"
docker-compose up -d db redis
sleep 10

echo -e "${YELLOW}🔄 Running database migrations...${NC}"
docker-compose run --rm app python migrate_database.py

echo -e "${YELLOW}🌱 Seeding initial data...${NC}"
docker-compose run --rm app python seed_data.py

echo -e "${YELLOW}🚀 Starting all services...${NC}"
docker-compose up -d

echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
sleep 15

# Health check
echo -e "${YELLOW}🏥 Checking application health...${NC}"
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$HEALTH_CHECK" -eq 200 ]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo -e "${GREEN}🌐 Application is running at: http://localhost:8000${NC}"
    echo -e "${GREEN}📚 API Documentation: http://localhost:8000/docs${NC}"
else
    echo -e "${RED}❌ Deployment failed! Health check returned: $HEALTH_CHECK${NC}"
    echo -e "${YELLOW}📋 Checking logs...${NC}"
    docker-compose logs app
    exit 1
fi

# Show running containers
echo -e "${YELLOW}📊 Running containers:${NC}"
docker-compose ps

echo -e "${GREEN}🎉 Deployment complete!${NC}"
# ---------- END OF FILE ----------