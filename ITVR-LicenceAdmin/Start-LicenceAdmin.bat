@echo off
chcp 65001 >nul
title ITVR Licence Admin
cd /d "%~dp0"

REM Use a local venv so dependencies are self-contained.
if not exist "venv\Scripts\python.exe" (
  echo Setting up (first run only)...
  python -m venv venv
  venv\Scripts\python.exe -m pip install --quiet --upgrade pip
  venv\Scripts\python.exe -m pip install --quiet flask bcrypt cryptography
)

echo Starting ITVR Licence Admin...
venv\Scripts\python.exe admin.py
pause
