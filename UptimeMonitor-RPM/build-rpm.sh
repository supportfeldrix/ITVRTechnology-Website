#!/bin/bash
# ============================================================
# Build the Uptime Monitoring RPM.
#
# RUN THIS ON A LINUX BOX (RHEL / Rocky / AlmaLinux / Fedora).
# It cannot be built on Windows — rpmbuild is Linux-only.
#
# Prerequisites (one-time, as root or with sudo):
#   RHEL/Rocky/Alma:  sudo dnf install -y rpm-build rpmdevtools
#   Fedora:           sudo dnf install -y rpm-build rpmdevtools
#
# Usage:
#   1. Copy this whole UptimeMonitor-RPM folder to the Linux box.
#   2. cd into it.
#   3. bash build-rpm.sh
#   The finished .rpm is printed at the end and left in ./out/.
# ============================================================
set -e

NAME="uptime-monitor"
VERSION="1.0.0"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building ${NAME}-${VERSION} RPM..."

# 1. Set up a clean rpmbuild tree under this folder.
TOP="$HERE/rpmbuild"
rm -rf "$TOP"
mkdir -p "$TOP"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# 2. Make the source tarball the spec expects: <name>-<version>.tar.gz
#    whose top-level folder is <name>-<version>/.
STAGE="$HERE/.stage/${NAME}-${VERSION}"
rm -rf "$HERE/.stage"
mkdir -p "$STAGE"
cp -a "$HERE/payload/." "$STAGE/"
# Never ship stray caches/venvs if present.
find "$STAGE" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf "$STAGE/venv" 2>/dev/null || true

tar -czf "$TOP/SOURCES/${NAME}-${VERSION}.tar.gz" -C "$HERE/.stage" "${NAME}-${VERSION}"
cp "$HERE/${NAME}.spec" "$TOP/SPECS/"

# 3. Build.
rpmbuild --define "_topdir $TOP" -bb "$TOP/SPECS/${NAME}.spec"

# 4. Collect the result.
mkdir -p "$HERE/out"
find "$TOP/RPMS" -name '*.rpm' -exec cp {} "$HERE/out/" \;

rm -rf "$HERE/.stage"

echo ""
echo "============================================================"
echo "  Build complete. RPM(s):"
ls -1 "$HERE/out/"*.rpm
echo ""
echo "  Install with:   sudo dnf install ./out/${NAME}-${VERSION}-1.*.rpm"
echo "  (or:            sudo rpm -i ./out/${NAME}-${VERSION}-1.*.rpm )"
echo "============================================================"
