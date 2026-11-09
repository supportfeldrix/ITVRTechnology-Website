# Server Agent Installation Guide

The server agent is a lightweight Python script that runs on each monitored
server and reports live metrics to the dashboard every 60 seconds.

**What it collects:**
- OS name/version and kernel
- CPU usage %, cores/threads
- RAM usage (used / total GB + %)
- Disk usage per mount (used / total GB + %)
- System uptime, load averages, running process count
- OS patch status (pending updates, reboot-required)

**Requirements:**
- Python 3.6+ (standard on modern RHEL/Ubuntu) — or use `agent_py27.py` for Python 2.7 hosts
- Network access from the server to your dashboard URL
- No root / sudo required; no extra Python packages (standard library only)

---

## Step 1 — Add the server in the dashboard

1. Open your dashboard and log in.
2. **Server Inventory → + Add Server**.
3. Fill in hostname, IP, environment, OS, role (specs optional).
4. **Save Server**.

## Step 2 — Get the agent token

Open the server's card → **Agent Setup**. The popup shows a unique token and
ready-to-copy install commands. (Tokens are issued through the dashboard — there
is no need to touch the database directly.)

## Step 3 — Copy the agent to the server

```bash
scp LINUX_SETUP/agent.py USER@TARGET_HOST:/opt/uptime-agent/agent.py
```

## Step 4 — Test it

```bash
python3 /opt/uptime-agent/agent.py \
  --url https://your-monitor-host:PORT \
  --token YOUR_TOKEN \
  --once
```

Expected: a line ending in `OK — CPU:.. RAM:.. Disk:..`. Refresh the dashboard —
the server card should show **● Agent online**.

## Step 5 — Schedule it (choose one)

### Option A — cron (simplest)
```bash
(crontab -l 2>/dev/null; echo "* * * * * python3 /opt/uptime-agent/agent.py --url https://your-monitor-host:PORT --token YOUR_TOKEN --once >> /opt/uptime-agent/agent.log 2>&1") | crontab -
```

### Option B — systemd user service (auto-restart, survives logout with linger)
```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/uptime-agent.service << 'EOF'
[Unit]
Description=Uptime Server Agent
After=network.target

[Service]
ExecStart=python3 /opt/uptime-agent/agent.py --url https://your-monitor-host:PORT --token YOUR_TOKEN
Restart=always
RestartSec=60

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now uptime-agent
```

### Option C — nohup (last resort; does not survive reboot)
```bash
nohup python3 /opt/uptime-agent/agent.py --url https://your-monitor-host:PORT --token YOUR_TOKEN --interval 60 >> /opt/uptime-agent/agent.log 2>&1 &
```

---

## Command reference

```
python3 agent.py [OPTIONS]
  --url URL          Dashboard URL (required)
  --token TOKEN      Agent token from the dashboard (required)
  --once             Run once and exit (for cron)
  --interval N       Loop interval in seconds (default: 60)
  --verify-ssl       Verify the TLS certificate (default: off for self-signed)
```

### Optional: monitor specific processes
Set `AGENT_PROCESS_CONFIG` to watch app processes `systemctl` doesn't list
(entries separated by `;;`, fields `name|pattern|ports|critical`):
```bash
AGENT_PROCESS_CONFIG="MyApp|com.example.MyApp|8080|true" \
  python3 agent.py --url https://your-monitor-host:PORT --token YOUR_TOKEN --once
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Invalid token` | Wrong/expired token | Regenerate via the Agent Setup button |
| `Connection refused` | Dashboard not reachable | Check the URL/port and that the app is running |
| `SSL error` | Self-signed certificate | The agent ignores TLS verification by default |
| `No such file` | agent.py not copied | Re-run the scp from Step 3 |
| Grey "No agent" dot | No recent data | Confirm the schedule is running: `ps aux \| grep agent.py` |

---

## Windows servers

Use the Windows agent instead — see `WINDOWS_AGENT/WINDOWS_AGENT_INSTALL.md`.
Quick install:
```powershell
.\install_agent.ps1 -Token "YOUR_TOKEN" -Url "https://your-monitor-host:PORT"
```
