# Uptime Monitoring — RPM package

Builds a native `.rpm` that installs Uptime Monitoring as a systemd service on
RHEL / Rocky / AlmaLinux / Fedora.

## What the RPM does

- Installs the app to `/opt/uptime-monitor`
- Creates a service account `uptimemon` (no login)
- Builds a Python virtual environment and installs dependencies on install
- Registers and starts a **systemd** service `uptime-monitor` (auto-starts on boot)
- Listens on **port 5000** (plain HTTP by default)
- Stores data (database, keys, logs) in `/opt/uptime-monitor/data`

## Build it (on a Linux box)

> The `.rpm` must be built on Linux — `rpmbuild` doesn't run on Windows.

```bash
# One-time: install build tools
sudo dnf install -y rpm-build rpmdevtools

# Copy this whole UptimeMonitor-RPM folder to the Linux box, then:
cd UptimeMonitor-RPM
bash build-rpm.sh
```

The finished package lands in `./out/uptime-monitor-1.0.0-1.*.rpm`.

## Install it (on the target server)

```bash
sudo dnf install ./uptime-monitor-1.0.0-1.*.rpm
```

On install it sets up the venv, starts the service, and prints the URL. Then:

1. Open `http://<server-ip>:5000/` in a browser.
2. Create your admin account on the first-run screen.
3. Set your branding and add monitors.

## Manage the service

```bash
systemctl status uptime-monitor      # health
systemctl restart uptime-monitor     # restart
journalctl -u uptime-monitor -f      # live logs
```

## Configuration (optional)

Create `/opt/uptime-monitor/data/uptime-monitor.env` to override defaults
(the service reads it automatically). Example:

```
PORT=8080
APP_BASE_URL=https://monitor.example.com
# COOKIE_SECURE=true   # set when you put HTTPS in front
```

Then `sudo systemctl restart uptime-monitor`.

## HTTPS

By default the service serves plain HTTP on port 5000. For HTTPS, put nginx in
front using the template at
`/opt/uptime-monitor/LINUX_SETUP/nginx-uptime-monitor.conf`
(set your `server_name` and certificate paths), and set `COOKIE_SECURE=true`
in the env file above.

## Upgrade

```bash
sudo dnf upgrade ./uptime-monitor-<new-version>.rpm
```
Your data in `/opt/uptime-monitor/data` is preserved.

## Uninstall

```bash
sudo dnf remove uptime-monitor
```
This stops/removes the service and the app. Your data directory
(`/opt/uptime-monitor/data`) is **left in place** on purpose — delete it
manually if you want to erase everything.

## OFFLINE / air-gapped servers

The install step runs `pip install` from PyPI. If the target server has no
internet:

1. On a machine **with** internet and the same OS/Python, download the wheels:
   ```bash
   mkdir wheels
   pip download -r /opt/uptime-monitor/requirements.txt gunicorn==21.2.0 -d wheels
   ```
2. Copy `wheels/` to the server.
3. After installing the RPM (the venv step will fail without internet — that's
   fine), finish the venv manually:
   ```bash
   cd /opt/uptime-monitor
   sudo ./venv/bin/pip install --no-index --find-links=/path/to/wheels -r requirements.txt gunicorn==21.2.0
   sudo systemctl restart uptime-monitor
   ```

(If offline installs are common for your users, tell us and we can ship a
version of the RPM with the wheels bundled inside so no internet is needed.)

## Free vs PRO

Free tier allows up to 4 monitors. PRO unlocks unlimited monitors via a licence
key entered under **Settings → About → Licence & Plan**. Contact
info@itvrtechnology.co.za for a key.
