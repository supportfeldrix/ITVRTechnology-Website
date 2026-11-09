#!/bin/bash
# ============================================================
# Uptime Monitoring — Update Script
# Copies updated app files, preserves the database, secret.key,
# encryption.key and .env, then restarts.  Usage: bash update.sh
# ============================================================
set -e

APP_DIR="$HOME/uptime-monitor"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_SOURCE="$(dirname "$SCRIPT_DIR")"

echo "[1/4] Backing up database..."
cp "$APP_DIR/uptime.db" "$APP_DIR/backups/uptime_pre_update_$(date +%Y%m%d_%H%M%S).db" 2>/dev/null || true

echo "[2/4] Stopping service..."
bash "$APP_DIR/stop.sh" 2>/dev/null || true
sleep 1

echo "[3/4] Copying updated files (preserves uptime.db, secret.key, encryption.key, .env)..."
cp "$APP_SOURCE/app.py"       "$APP_DIR/"
cp -r "$APP_SOURCE/frontend/" "$APP_DIR/"
cp -r "$APP_SOURCE/logo/"     "$APP_DIR/"
"$APP_DIR/venv/bin/pip" install --quiet -r "$APP_SOURCE/requirements.txt" 2>/dev/null || true

echo "[4/4] Restarting service..."
bash "$APP_DIR/start.sh"
echo "Update complete."
