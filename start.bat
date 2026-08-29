@echo off
setlocal enabledelayedexpansion

:: ============================================================
::   TOBI Launch Script  (Windows)
::   Usage:  start.bat [text|voice|server|full]
::   Default: server  (API + UI, no local mic — safest for testing)
:: ============================================================

set SCRIPT_DIR=%~dp0
set UI_DIR=%SCRIPT_DIR%Tobi\ui\tobi-ui
set MODE=%1
if "%MODE%"=="" set MODE=server

echo.
echo ============================================================
echo   TOBI  ^|  Mode: %MODE%
echo ============================================================
echo.

:: ── Check .env ───────────────────────────────────────────────
if not exist "%SCRIPT_DIR%.env" (
    echo [WARN] No .env file found. Run setup.bat first, or copy .env.example to .env
    copy "%SCRIPT_DIR%.env.example" "%SCRIPT_DIR%.env" >nul
    echo [OK]   Created .env with demo values. AI responses disabled until you set ANTHROPIC_API_KEY.
)

:: ── Data directories ─────────────────────────────────────────
if not exist "%SCRIPT_DIR%data" mkdir "%SCRIPT_DIR%data"
if not exist "%SCRIPT_DIR%data\logs" mkdir "%SCRIPT_DIR%data\logs"
if not exist "%SCRIPT_DIR%data\memory" mkdir "%SCRIPT_DIR%data\memory"
if not exist "%SCRIPT_DIR%data\reminder_audio" mkdir "%SCRIPT_DIR%data\reminder_audio"

:: ── Start UI (all modes except text and voice) ───────────────
if /i "%MODE%"=="text" goto :backend
if /i "%MODE%"=="voice" goto :backend

echo [1/2] Starting frontend on http://localhost:3741 ...
cd /d "%UI_DIR%"
start "TOBI UI" /min cmd /c "npm run dev 2>&1 | findstr /v warn"
cd /d "%SCRIPT_DIR%"

echo       Waiting for UI to boot...
timeout /t 6 /nobreak >nul

:: Open browser automatically
echo [OK]  Opening http://localhost:3741 in your browser...
start http://localhost:3741

:backend
:: ── Start backend ────────────────────────────────────────────
echo.
echo [2/2] Starting TOBI backend...
echo       API  : http://localhost:8741
echo       PIN  : 1234  ^(change TOBI_PIN in .env to customise^)
echo.
echo       Press Ctrl+C to stop TOBI.
echo.

python -m Tobi.main %MODE%

echo.
echo TOBI stopped.
pause
