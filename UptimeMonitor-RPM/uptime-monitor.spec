Name:           uptime-monitor
Version:        1.0.0
Release:        1%{?dist}
Summary:        Uptime Monitoring — self-hosted uptime, database and server monitoring

License:        Proprietary
URL:            https://itvrtechnology.co.za
Vendor:         ITVR Technology
Packager:       ITVR Technology <info@itvrtechnology.co.za>

# The app source is delivered as a tarball built by build-rpm.sh.
Source0:        %{name}-%{version}.tar.gz

# No auto-dependency scanning of the bundled files.
AutoReqProv:    no

# Needs Python 3.9+ at runtime. The post-install creates a venv with pip.
Requires:       python3 >= 3.9
Requires:       python3-pip

# Where the app lives, who runs it, and the service port.
%global appdir   /opt/uptime-monitor
%global appuser  uptimemon
%global appport  5000

%description
Uptime Monitoring is a self-hosted dashboard for monitoring web apps, APIs,
databases and servers — with status pages, email alerts, SSL certificate
tracking, role-based access, dark mode and your own branding.

Installs to %{appdir}, runs as the '%{appuser}' service account under systemd,
and listens on port %{appport}. Free tier supports up to 4 monitors; PRO
unlocks unlimited monitors via a licence key.

By ITVR Technology — info@itvrtechnology.co.za

# ──────────────────────────────────────────────────────────────
%prep
%setup -q -n %{name}-%{version}

# ──────────────────────────────────────────────────────────────
%build
# Nothing to compile — the venv is created at install time (%post) so the
# package stays portable and small.

# ──────────────────────────────────────────────────────────────
%install
rm -rf %{buildroot}

# App files → /opt/uptime-monitor
mkdir -p %{buildroot}%{appdir}
cp -a app.py monitors.json requirements.txt %{buildroot}%{appdir}/
cp -a frontend logo LINUX_SETUP %{buildroot}%{appdir}/
cp -a MONITORING-GUIDE.md AGENT_INSTALL.md LICENSE.txt %{buildroot}%{appdir}/

# Writable data dir (database, keys, logs) — kept separate from app files.
mkdir -p %{buildroot}%{appdir}/data

# systemd unit
mkdir -p %{buildroot}%{_unitdir}
cat > %{buildroot}%{_unitdir}/uptime-monitor.service <<EOF
[Unit]
Description=Uptime Monitoring
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=%{appuser}
Group=%{appuser}
WorkingDirectory=%{appdir}
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONIOENCODING=utf-8
Environment=DATA_DIR=%{appdir}/data
Environment=DB_PATH=%{appdir}/data/uptime.db
Environment=HOST=0.0.0.0
Environment=PORT=%{appport}
# Plain HTTP by default (put nginx in front for HTTPS). Cookies over HTTP need:
Environment=COOKIE_SECURE=false
EnvironmentFile=-%{appdir}/data/uptime-monitor.env
ExecStart=%{appdir}/venv/bin/gunicorn --workers 1 --bind 0.0.0.0:%{appport} --timeout 120 --keep-alive 5 app:app
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# ──────────────────────────────────────────────────────────────
%pre
# Create the service user (system account, no login) if missing.
getent group %{appuser} >/dev/null || groupadd -r %{appuser}
getent passwd %{appuser} >/dev/null || \
    useradd -r -g %{appuser} -d %{appdir} -s /sbin/nologin \
            -c "Uptime Monitoring service account" %{appuser}

# ──────────────────────────────────────────────────────────────
%post
# Build the Python virtual environment and install dependencies.
# (Needs internet to PyPI. For offline servers, see the OFFLINE note in README.)
cd %{appdir}
python3 -m venv venv
./venv/bin/pip install --upgrade pip >/dev/null 2>&1 || true
./venv/bin/pip install -r requirements.txt
# gunicorn is the production server used by the systemd unit.
./venv/bin/pip install "gunicorn==21.2.0"

# Ownership: app read-only to the service user; data writable.
chown -R %{appuser}:%{appuser} %{appdir}
chmod 750 %{appdir}/data

# Enable + start the service.
%systemd_post uptime-monitor.service
systemctl daemon-reload
systemctl enable uptime-monitor.service >/dev/null 2>&1 || true
systemctl restart uptime-monitor.service || true

echo ""
echo "============================================================"
echo "  Uptime Monitoring installed."
echo "  Open http://<this-server>:%{appport}/ in a browser and"
echo "  create your admin account on the first screen."
echo ""
echo "  Service:  systemctl status uptime-monitor"
echo "  Logs:     journalctl -u uptime-monitor -f"
echo "  Config:   %{appdir}/data/uptime-monitor.env  (optional)"
echo "============================================================"
echo ""

# ──────────────────────────────────────────────────────────────
%preun
%systemd_preun uptime-monitor.service

# ──────────────────────────────────────────────────────────────
%postun
%systemd_postun_with_restart uptime-monitor.service
# On full uninstall (not upgrade), remove the venv we created.
if [ "$1" = "0" ]; then
    rm -rf %{appdir}/venv
    echo "Note: %{appdir}/data (your database and keys) was left in place."
    echo "Remove it manually if you want to erase all data."
fi

# ──────────────────────────────────────────────────────────────
%files
%defattr(-,root,root,-)
%dir %{appdir}
%{appdir}/app.py
%{appdir}/monitors.json
%{appdir}/requirements.txt
%{appdir}/frontend
%{appdir}/logo
%{appdir}/LINUX_SETUP
%{appdir}/MONITORING-GUIDE.md
%{appdir}/AGENT_INSTALL.md
%license %{appdir}/LICENSE.txt
%attr(0750,%{appuser},%{appuser}) %dir %{appdir}/data
%{_unitdir}/uptime-monitor.service

# ──────────────────────────────────────────────────────────────
%changelog
* Mon Nov 03 2026 ITVR Technology <info@itvrtechnology.co.za> - 1.0.0-1
- Initial RPM release: self-hosted Uptime Monitoring with systemd service,
  free/PRO licensing, first-run admin setup in the browser.
