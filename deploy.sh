#!/bin/bash

# Safe Deployment Script for URL Contact Crawler App
# This script ensures data is preserved during deployment

set -e  # Exit on any error

echo "🚀 Starting safe deployment..."

# Get the deployment directory (where the script is run from)
DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$DEPLOY_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Step 1: Backup existing data
echo "📦 Backing up existing data..."
if [ -f "$DEPLOY_DIR/schedule.db" ]; then
    cp "$DEPLOY_DIR/schedule.db" "$BACKUP_DIR/schedule_${TIMESTAMP}.db"
    echo "✅ Database backed up to: $BACKUP_DIR/schedule_${TIMESTAMP}.db"
fi

if [ -d "$DEPLOY_DIR/uploads" ] && [ "$(ls -A $DEPLOY_DIR/uploads 2>/dev/null)" ]; then
    tar -czf "$BACKUP_DIR/uploads_${TIMESTAMP}.tar.gz" -C "$DEPLOY_DIR" uploads/
    echo "✅ Uploads backed up to: $BACKUP_DIR/uploads_${TIMESTAMP}.tar.gz"
fi

# Step 2: Preserve data by moving to temporary location
echo "💾 Preserving current data..."
TEMP_DATA_DIR=$(mktemp -d)
if [ -f "$DEPLOY_DIR/schedule.db" ]; then
    mv "$DEPLOY_DIR/schedule.db" "$TEMP_DATA_DIR/"
fi
if [ -d "$DEPLOY_DIR/uploads" ]; then
    mv "$DEPLOY_DIR/uploads" "$TEMP_DATA_DIR/"
fi
if [ -f "$DEPLOY_DIR/.env" ]; then
    mv "$DEPLOY_DIR/.env" "$TEMP_DATA_DIR/"
fi

# Step 3: Pull latest code from GitHub
echo "📥 Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/main

# Step 4: Restore data
echo "♻️  Restoring preserved data..."
if [ -f "$TEMP_DATA_DIR/schedule.db" ]; then
    rm -f "$DEPLOY_DIR/schedule.db"
    mv "$TEMP_DATA_DIR/schedule.db" "$DEPLOY_DIR/"
fi
if [ -d "$TEMP_DATA_DIR/uploads" ]; then
    rm -rf "$DEPLOY_DIR/uploads"
    mv "$TEMP_DATA_DIR/uploads" "$DEPLOY_DIR/"
else
    mkdir -p "$DEPLOY_DIR/uploads"
fi
if [ -f "$TEMP_DATA_DIR/.env" ]; then
    rm -f "$DEPLOY_DIR/.env"
    mv "$TEMP_DATA_DIR/.env" "$DEPLOY_DIR/"
fi

# Clean up temp directory
rm -rf "$TEMP_DATA_DIR"

# Step 5: Install/update dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt --quiet 2>/dev/null || pip install -r requirements.txt --quiet --break-system-packages

# Step 6: Restart application (uncomment the method you use)
echo "🔄 Restarting application..."

# If using systemd:
# sudo systemctl restart your-app-name

# If using gunicorn with supervisor:
# sudo supervisorctl restart your-app-name

# If using PM2:
# pm2 restart app

# If running with gunicorn manually, you'll need to kill and restart:
# pkill -f "gunicorn.*app:app" || true
# nohup gunicorn -w 4 -b 0.0.0.0:8000 app:app > logs/gunicorn.log 2>&1 &

echo "✅ Deployment complete!"
echo "📊 Your data has been preserved:"
echo "   - Database: $([ -f "$DEPLOY_DIR/schedule.db" ] && echo "✓" || echo "✗") schedule.db"
echo "   - Uploads: $([ -d "$DEPLOY_DIR/uploads" ] && echo "✓" || echo "✗") uploads/"
echo "   - Backups: $BACKUP_DIR/"
echo ""
echo "💡 To restore from backup if needed:"
echo "   cp $BACKUP_DIR/schedule_${TIMESTAMP}.db schedule.db"
echo "   tar -xzf $BACKUP_DIR/uploads_${TIMESTAMP}.tar.gz"
