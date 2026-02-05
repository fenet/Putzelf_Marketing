#!/bin/bash

# Quick Backup Script for Production Data
# Run this BEFORE deploying or pulling code changes

set -e

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup at: $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Backup database
if [ -f "schedule.db" ]; then
    cp "schedule.db" "$BACKUP_DIR/schedule_${TIMESTAMP}.db"
    DB_SIZE=$(du -h "$BACKUP_DIR/schedule_${TIMESTAMP}.db" | cut -f1)
    echo "✅ Database backed up: schedule_${TIMESTAMP}.db ($DB_SIZE)"
else
    echo "⚠️  schedule.db not found"
fi

# Backup uploads
if [ -d "uploads" ] && [ "$(ls -A uploads 2>/dev/null)" ]; then
    tar -czf "$BACKUP_DIR/uploads_${TIMESTAMP}.tar.gz" uploads/
    UPLOAD_SIZE=$(du -h "$BACKUP_DIR/uploads_${TIMESTAMP}.tar.gz" | cut -f1)
    echo "✅ Uploads backed up: uploads_${TIMESTAMP}.tar.gz ($UPLOAD_SIZE)"
else
    echo "⚠️  uploads directory is empty or not found"
fi

# Backup .env if exists
if [ -f ".env" ]; then
    cp ".env" "$BACKUP_DIR/.env_${TIMESTAMP}"
    echo "✅ Environment file backed up: .env_${TIMESTAMP}"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💾 All backups stored in: $BACKUP_DIR/"
echo ""
echo "📋 Backup List:"
ls -lh "$BACKUP_DIR/" | tail -n +2 | awk '{print "   " $9 " (" $5 ")"}'
echo ""
echo "✅ Backup complete! Safe to proceed with: git pull origin main"
