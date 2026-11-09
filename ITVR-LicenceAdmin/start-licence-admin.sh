#!/bin/bash
# ============================================================
# ITVR Licence Admin — launcher for Linux / Fedora
# Runs the local key-generator + client log on your own machine.
# Usage:  bash start-licence-admin.sh    (or: ./start-licence-admin.sh)
# ============================================================
set -e
cd "$(dirname "$0")"

# First run: create a local venv and install dependencies.
if [ ! -x "venv/bin/python" ]; then
  echo "Setting up (first run only)..."
  python3 -m venv venv
  ./venv/bin/pip install --quiet --upgrade pip
  ./venv/bin/pip install --quiet -r requirements.txt
fi

echo "Starting ITVR Licence Admin..."
exec ./venv/bin/python admin.py
