#!/bin/bash
# ============================================================
# Uptime Monitoring — Deployment Script (no sudo required)
# Run as the service user that should own the app:  bash deploy.sh
# Installs into $HOME/uptime-monitor and starts Gunicorn.
# ============================================================
set -e

APP_DIR="$HOME/uptime-monitor"
PID_FILE="$APP_DIR/uptime-monitor.pid"
LOG_FILE="$APP_DIR/logs/gunicorn.log"
PORT="${PORT:-5000}"

echo ""
echo "============================================================"
echo "  Uptime Monitoring — Deployment"
echo "============================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_SOURCE="$(dirname "$SCRIPT_DIR")"

echo "[1/5] Creating application directory..."
mkdir -p "$APP_DIR/frontend/dist" "$APP_DIR/logo" "$APP_DIR/logs" "$APP_DIR/backups"

echo "[2/5] Copying application files..."
cp "$APP_SOURCE/app.py"        "$APP_DIR/"
cp "$APP_SOURCE/monitors.json" "$APP_DIR/" 2>/dev/null || true
cp -r "$APP_SOURCE/frontend/"  "$APP_DIR/"
cp -r "$APP_SOURCE/logo/"      "$APP_DIR/"
# Carry over config if present (never overwrite an existing one)
[ -f "$APP_SOURCE/.env" ] && [ ! -f "$APP_DIR/.env" ] && cp "$APP_SOURCE/.env" "$APP_DIR/.env" || true

echo "[3/5] Creating Python virtual environment..."
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/venv/bin/pip" install --quiet -r "$APP_SOURCE/requirements.txt"

echo "[4/5] Installing helper scripts..."
cp "$SCRIPT_DIR/backup.sh" "$APP_DIR/backup.sh"
cp "$SCRIPT_DIR/update.sh" "$APP_DIR/update.sh"
chmod +x "$APP_DIR/backup.sh" "$APP_DIR/update.sh"

cat > "$APP_DIR/start.sh" << EOF
#!/bin/bash
APP_DIR="\$(cd "\$(dirname "\$0")" && pwd)"
PID_FILE="\$APP_DIR/uptime-monitor.pid"
LOG_FILE="\$APP_DIR/logs/gunicorn.log"
if [ -f "\$PID_FILE" ] && kill -0 "\$(cat "\$PID_FILE")" 2>/dev/null; then
  kill "\$(cat "\$PID_FILE")"; sleep 2; rm -f "\$PID_FILE"
fi
cd "\$APP_DIR"
nohup "\$APP_DIR/venv/bin/gunicorn" --workers 1 --bind 0.0.0.0:${PORT} \\
  --timeout 120 --keep-alive 5 --pid "\$PID_FILE" \\
  --access-logfile "\$LOG_FILE" --error-logfile "\$LOG_FILE" --log-level info \\
  app:app >> "\$LOG_FILE" 2>&1 &
sleep 2
echo "Started on port ${PORT}. Logs: tail -f \$LOG_FILE"
EOF
chmod +x "$APP_DIR/start.sh"

cat > "$APP_DIR/stop.sh" << 'EOF'
#!/bin/bash
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$APP_DIR/uptime-monitor.pid"
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  kill "$(cat "$PID_FILE")"; rm -f "$PID_FILE"; echo "Stopped."
else
  echo "Not running."; rm -f "$PID_FILE" 2>/dev/null || true
fi
EOF
chmod +x "$APP_DIR/stop.sh"

echo "[5/5] Starting the application..."
bash "$APP_DIR/start.sh"

echo ""
echo "============================================================"
echo "  Deployment complete."
echo "  On first run the console prints the initial admin password."
echo "  Start:  bash $APP_DIR/start.sh"
echo "  Stop:   bash $APP_DIR/stop.sh"
echo "  Logs:   tail -f $LOG_FILE"
echo ""
echo "  For production HTTPS, put nginx-uptime-monitor.conf in front,"
echo "  or run gunicorn with --certfile/--keyfile. See README.md."
echo "============================================================"
