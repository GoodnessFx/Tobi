@echo off
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   TOBI Setup  ^(Windows^)
echo   Total Omni Brain Intelligence
echo ============================================================
echo.

:: ── Python check ────────────────────────────────────────────
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Install Python 3.11+ from https://python.org
    echo         Make sure to check "Add Python to PATH" during install.
    pause & exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] Python %PY_VER%

:: ── Node check ──────────────────────────────────────────────
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js not found. Install Node 18+ from https://nodejs.org
    pause & exit /b 1
)
for /f %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo [OK] Node %NODE_VER%

:: ── .env file ───────────────────────────────────────────────
if not exist ".env" (
    copy .env.example .env >nul
    echo [OK] Created .env from .env.example
    echo.
    echo  *** IMPORTANT ***
    echo  Open .env and set your ANTHROPIC_API_KEY.
    echo  Get a key at: https://console.anthropic.com
    echo  Without it, TOBI runs but AI replies will be disabled.
    echo.
) else (
    echo [OK] .env already exists
)

:: ── Python dependencies ──────────────────────────────────────
echo.
echo [1/3] Installing Python dependencies...
pip install -r requirements.txt -q
if %ERRORLEVEL% neq 0 (
    echo [ERROR] pip install failed. Try: pip install -r requirements.txt
    pause & exit /b 1
)
echo [OK] Python dependencies installed

echo.
echo [Optional] Attempting to install wake-word dependencies ^(requires Python ^= 3.11^)...
pip install -r requirements-voice-wakeword.txt -q
if %ERRORLEVEL% neq 0 (
    echo [WARN] Wake-word dependencies failed to install. Push-to-talk voice will still work.
) else (
    echo [OK] Wake-word dependencies installed
)

:: ── Frontend dependencies ────────────────────────────────────
echo.
echo [2/3] Installing frontend dependencies ^(this takes ~2 minutes first time^)...
cd /d "%~dp0Tobi\ui\tobi-ui"
npm install --silent
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm install failed.
    pause & exit /b 1
)
cd /d "%~dp0"
echo [OK] Frontend dependencies installed

:: ── Playwright (browser automation) ─────────────────────────
echo.
echo [3/3] Installing Playwright Chromium for browser automation...
playwright install chromium --quiet 2>nul
if %ERRORLEVEL% neq 0 (
    echo [WARN] Playwright install failed ^(browser automation disabled^). TOBI still works.
) else (
    echo [OK] Playwright installed
)

:: ── PC Wake Setup (Windows) ──────────────────────────────────
echo.
echo Setting up OS wake permissions for alarms...
powershell -Command "$action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c exit'; $trigger = New-ScheduledTaskTrigger -Once -At '00:00'; $settings = New-ScheduledTaskSettingsSet -WakeToRun; Register-ScheduledTask -TaskName 'TobiWake' -Action $action -Trigger $trigger -Settings $settings -Force" >nul 2>&1
echo [OK] Scheduled task 'TobiWake' created for PC wake functionality.

:: ── Data directories ─────────────────────────────────────────
if not exist "data" mkdir data
if not exist "data\logs" mkdir data\logs
if not exist "data\memory" mkdir data\memory
if not exist "data\reminder_audio" mkdir data\reminder_audio

echo.
echo ============================================================
echo   Setup complete!
echo.
echo   To start TOBI:   start.bat
echo   Then open:        http://localhost:3741
echo   Default PIN:      1234
echo ============================================================
echo.
pause
