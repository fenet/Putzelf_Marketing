# Safe Deployment Guide

## Overview
This guide ensures your data (database and uploads) is preserved during deployments.

## Quick Deployment

### Method 1: Using the Deploy Script (Recommended)
```bash
chmod +x deploy.sh
./deploy.sh
```

### Method 2: Manual Deployment
```bash
# 1. Backup data
cp schedule.db backups/schedule_$(date +%Y%m%d_%H%M%S).db
tar -czf backups/uploads_$(date +%Y%m%d_%H%M%S).tar.gz uploads/

# 2. Pull latest code
git pull origin main

# 3. Install dependencies
pip install -r requirements.txt

# 4. Restart your application
# (use your specific restart command)
```

## Data Protection Strategy

### 1. Files Excluded from Git (.gitignore)
These files are NEVER pushed to GitHub and stay on your server:
- `schedule.db` - Your SQLite database
- `uploads/*` - User uploaded files
- `.env` - Environment variables and secrets

### 2. Backup System
The deploy script creates timestamped backups in `backups/` directory:
- Database: `schedule_YYYYMMDD_HHMMSS.db`
- Uploads: `uploads_YYYYMMDD_HHMMSS.tar.gz`

### 3. Restore from Backup
If something goes wrong:
```bash
# Restore database
cp backups/schedule_YYYYMMDD_HHMMSS.db schedule.db

# Restore uploads
tar -xzf backups/uploads_YYYYMMDD_HHMMSS.tar.gz
```

## Production Server Setup

### Environment Variables
Create a `.env` file on your production server:
```bash
DATABASE_URL=sqlite:///schedule.db
AUTH_USERNAME=your_admin_username
AUTH_PASSWORD=your_secure_password
FLASK_SECRET_KEY=your-secret-key-here

# SMTP (invoice emails)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USERNAME=your-email@domain.com
SMTP_PASSWORD=your-smtp-password-or-app-password
SENDER_EMAIL=your-email@domain.com
SENDER_NAME=Your Company Name
```

### Directory Structure
```
/path/to/app/
├── app.py
├── requirements.txt
├── .env                    # Not in git
├── schedule.db            # Not in git
├── uploads/               # Not in git
│   └── (user files)
├── backups/               # Not in git
│   ├── schedule_*.db
│   └── uploads_*.tar.gz
└── static/
```

## Deployment Checklist

Before deploying:
- [ ] Ensure `.gitignore` excludes data files
- [ ] Verify `.env` file exists on production server
- [ ] Run the deploy script or manual backup
- [ ] Test the application after deployment
- [ ] Verify data is intact

## Common Issues

### Issue: "Data still gets deleted"
**Solution:** Make sure `schedule.db` and `uploads/` are in `.gitignore`

### Issue: "Permission denied"
**Solution:** Make deploy script executable: `chmod +x deploy.sh`

### Issue: "Need to migrate to PostgreSQL"
**Solution:** Set `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

## Advanced: Using PostgreSQL (Recommended for Production)

For better data safety, consider migrating to PostgreSQL:

1. Install PostgreSQL on your server
2. Create a database:
```bash
sudo -u postgres createdb crawler_app
```

3. Update `.env`:
```
DATABASE_URL=postgresql://username:password@localhost/crawler_app
```

4. Migrate data:
```bash
# Install migration tool
pip install sqlalchemy-utils

# Run migration (you may need a custom script)
python migrate_db.py
```

## Automated Backups

Set up a cron job for regular backups:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/app/deploy.sh backup-only
```

## Support

If you encounter issues:
1. Check backup files in `backups/` directory
2. Review application logs
3. Verify `.env` file configuration
4. Ensure proper file permissions
