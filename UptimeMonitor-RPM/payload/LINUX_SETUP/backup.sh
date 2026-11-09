#!/bin/bash
# ============================================================
# Uptime Monitoring — Database Backup Script
# Schedule via cron, e.g. daily at 02:00:
#   0 2 * * * bash /opt/uptime-monitor/backup.sh >> /opt/uptime-monitor/logs/backup.log 2>&1
# ============================================================

APP_DIR="${APP_DIR:-$HOME/uptime-monitor}"
BACKUP_DIR="$APP_DIR/backups"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS="${KEEP_DAYS:-30}"

mkdir -p "$BACKUP_DIR"
echo "[$DATE] Starting backup..."

BACKUP_FILE="$BACKUP_DIR/uptime_${DATE}.db"
cp "$APP_DIR/uptime.db" "$BACKUP_FILE"

if [ $? -eq 0 ]; then
  gzip "$BACKUP_FILE"
  echo "[$DATE] Backup created: ${BACKUP_FILE}.gz"
else
  echo "[$DATE] ERROR: Backup failed!"; exit 1
fi

find "$BACKUP_DIR" -name "uptime_*.db.gz" -mtime +"$KEEP_DAYS" -delete
echo "[$DATE] Old backups cleaned (kept last $KEEP_DAYS days). Backup complete."
