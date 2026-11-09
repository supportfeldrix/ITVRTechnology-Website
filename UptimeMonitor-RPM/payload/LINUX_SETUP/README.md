# Uptime Monitoring — Linux Setup

Run the dashboard on a Linux host (no sudo required for the no-sudo path below).

## What's in this folder

| File | Purpose |
|------|---------|
| `deploy.sh` | One-time deployment (creates `~/uptime-monitor`, venv, start/stop scripts) |
| `update.sh` | Copy updated app files and restart (preserves DB and keys) |
| `backup.sh` | Database backup script (schedule via cron) |
| `uptime-monitor.service` | systemd unit template (edit the `User`/`Group`) |
| `nginx-uptime-monitor.conf` | Nginx reverse-proxy example for HTTPS |
| `agent.py` | Linux server agent (Python 3) |
| `agent_py27.py` | Linux server agent (Python 2.7 compatible, for older hosts) |
| `collect_metrics_linux.sh` | Shell metrics collector (for SSH/agentless collection) |

## Quick deploy (no sudo)

```bash
# As the service user that should own the app:
cd LINUX_SETUP
bash deploy.sh
```

This creates `~/uptime-monitor`, sets up a venv, installs dependencies, writes
`start.sh`/`stop.sh`, and starts the app on port 5000 (override with `PORT=8080 bash deploy.sh`).

On **first run** the console prints the initial admin credentials — save them and
change the password after logging in. Configure the app via a `.env` file
(see `../.env.example`).

## Production (systemd + nginx)

1. Install the app under `/opt/uptime-monitor` (adjust paths to taste).
2. Edit `uptime-monitor.service` — set `User`/`Group` to your service account —
   then install it:
   ```bash
   sudo cp uptime-monitor.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now uptime-monitor
   ```
3. Put nginx in front for HTTPS: edit `nginx-uptime-monitor.conf` (server_name,
   SSL cert paths), copy it to `/etc/nginx/conf.d/`, then `sudo nginx -t && sudo systemctl reload nginx`.

## Backups

Schedule `backup.sh` via cron:
```
0 2 * * * bash /opt/uptime-monitor/backup.sh >> /opt/uptime-monitor/logs/backup.log 2>&1
```
Also back up `secret.key` and `encryption.key` (losing the latter means stored
database-monitor passwords can't be decrypted).

## Installing the server agent

The agent reports a server's OS/CPU/RAM/disk metrics to the dashboard.

1. In the dashboard: **Server Inventory → Add Server**, then open the server and
   use **Agent Setup** to generate a token.
2. Copy `agent.py` (or `agent_py27.py` for Python 2.7 hosts) to the server.
3. Run it, pointing at your dashboard URL:
   ```bash
   python3 agent.py --url https://your-monitor-host:PORT --token YOUR_TOKEN --once
   ```
4. Schedule it every minute via cron:
   ```
   * * * * * python3 /opt/uptime-agent/agent.py --url https://your-monitor-host:PORT --token YOUR_TOKEN --once >> /opt/uptime-agent/agent.log 2>&1
   ```

### Optional: monitor specific processes

To watch application processes that `systemctl` doesn't list, set
`AGENT_PROCESS_CONFIG` when running the agent (entries separated by `;;`,
fields `name|pattern|ports|critical`):

```bash
AGENT_PROCESS_CONFIG="MyApp|com.example.MyApp|8080|true;;Worker|myworker|9000|false" \
  python3 agent.py --url https://your-monitor-host:PORT --token YOUR_TOKEN --once
```
By default this is empty and no process monitoring happens.
