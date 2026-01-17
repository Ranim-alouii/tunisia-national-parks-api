#!/bin/bash

# Tunisia Parks Backup Script
# Usage: ./backup.sh [backup_name]

set -e

BACKUP_NAME=${1:-$(date +"%Y%m%d_%H%M%S")}
BACKUP_DIR="./backups"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

echo "💾 Creating backup: $BACKUP_NAME"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}📁 Creating backup directory: $BACKUP_PATH${NC}"
mkdir -p "$BACKUP_PATH"

# Backup database
if [ -f "tunisia_parks.db" ]; then
    echo -e "${BLUE}💾 Backing up database...${NC}"
    cp tunisia_parks.db "$BACKUP_PATH/tunisia_parks.db"
    echo -e "${GREEN}✅ Database backed up${NC}"
else
    echo -e "${YELLOW}⚠️  Database file not found${NC}"
fi

# Backup uploads
if [ -d "uploads" ]; then
    echo -e "${BLUE}📸 Backing up uploads...${NC}"
    cp -r uploads "$BACKUP_PATH/uploads"
    echo -e "${GREEN}✅ Uploads backed up${NC}"
else
    echo -e "${YELLOW}⚠️  Uploads directory not found${NC}"
fi

# Backup environment files (without secrets)
echo -e "${BLUE}🔧 Backing up configuration...${NC}"
cp .env "$BACKUP_PATH/.env.backup" 2>/dev/null || echo "No .env file to backup"
cp docker-compose.yml "$BACKUP_PATH/docker-compose.yml" 2>/dev/null || echo "No docker-compose.yml to backup"

# Create backup info
cat > "$BACKUP_PATH/BACKUP_INFO.txt" << EOF
Tunisia Parks Backup Information
================================

Backup Name: $BACKUP_NAME
Created: $(date)
Version: 3.0.0

Contents:
- Database: tunisia_parks.db
- Uploads: uploads/ directory
- Configuration: .env and docker-compose.yml

Restore Instructions:
1. Stop the application: docker-compose down
2. Restore database: cp $BACKUP_PATH/tunisia_parks.db ./
3. Restore uploads: cp -r $BACKUP_PATH/uploads ./
4. Start application: docker-compose up -d

Notes:
- This backup contains production data
- Test restoration in development environment first
- Keep backups in secure location
EOF

# Compress backup
echo -e "${BLUE}📦 Compressing backup...${NC}"
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
cd ..

# Calculate sizes
DB_SIZE=$(du -sh "$BACKUP_PATH/tunisia_parks.db" 2>/dev/null | cut -f1 || echo "N/A")
UPLOAD_SIZE=$(du -sh "$BACKUP_PATH/uploads" 2>/dev/null | cut -f1 || echo "N/A")
TOTAL_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)

echo -e "${GREEN}✅ Backup completed successfully!${NC}"
echo -e "${BLUE}📊 Backup Details:${NC}"
echo -e "   📁 Location: $BACKUP_PATH"
echo -e "   📦 Archive: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo -e "   💾 Database Size: $DB_SIZE"
echo -e "   📸 Uploads Size: $UPLOAD_SIZE"
echo -e "   📏 Total Size: $TOTAL_SIZE"

# Cleanup uncompressed backup
echo -e "${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -rf "$BACKUP_PATH"

# Show retention info
echo -e "${BLUE}📋 Backup Retention:${NC}"
echo -e "   • Keep last 7 daily backups"
echo -e "   • Keep last 4 weekly backups"
echo -e "   • Keep last 12 monthly backups"

# List recent backups
echo -e "${BLUE}📂 Recent Backups:${NC}"
ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -5 || echo "No previous backups found"

echo -e "${GREEN}🎉 Backup complete!${NC}"
