@echo off
setlocal

echo ============================================================
echo  Tobi Setup Script (Windows)
echo ============================================================

:: Check for Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    exit /b 1
)

:: Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

:: Install UI dependencies
echo Installing UI dependencies...
cd /d Tobi\ui\tobi-ui
npm install
cd /d ..\..\..

:: Install Playwright
echo Installing Playwright Chromium...
playwright install chromium

echo.
echo ============================================================
echo  Setup Complete!
echo  Run start.bat to launch Tobi.
echo ============================================================
pause
