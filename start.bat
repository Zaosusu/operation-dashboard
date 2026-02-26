@echo off
title Operation Dashboard

echo ========================================
echo   Operation Dashboard
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

echo Checking dependencies...

python -c "import os, json, sqlite3, hashlib, functools, datetime, flask, flask_cors" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install flask flask-cors -q
)

echo Starting server...
echo Local: http://localhost:5000
start http://localhost:5000
python server.py
