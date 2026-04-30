@echo off
setlocal enabledelayedexpansion

:: Tobi Launch Script for Windows
:: Usage: start.bat [text|voice|server|full]
:: Default: full (voice + API server + UI)

set SCRIPT_DIR=%~dp0
set UI_DIR=%SCRIPT_DIR%Tobi\ui\tobi-ui
set MODE=%1
if "%MODE%"=="" set MODE=full

echo ============================================================
echo  Tobi Launch Script (Windows)
echo  Mode: %MODE%
echo ============================================================

:: Check for Ollama
echo Checking for Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Ollama is not running. Attempting to start it...
    start /b ollama serve
    timeout /t 5 /nobreak >nul
)

:: Install Playwright if needed
echo Checking Playwright...
python -c "import playwright" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing Playwright...
    pip install playwright -q
    playwright install chromium
)

:: Create data directories
if not exist "%SCRIPT_DIR%data" mkdir "%SCRIPT_DIR%data"
if not exist "%SCRIPT_DIR%data\logs" mkdir "%SCRIPT_DIR%data\logs"
if not exist "%SCRIPT_DIR%templates\prompts" mkdir "%SCRIPT_DIR%templates\prompts"

:: Start UI if in full or server mode
if "%MODE%"=="full" (
    echo Starting Tobi UI on http://localhost:3000 ...
    cd /d "%UI_DIR%"
    start /b npm run dev -- --hostname 0.0.0.0 --port 3000
    cd /d "%SCRIPT_DIR%"
    timeout /t 5 /nobreak >nul
)

if "%MODE%"=="server" (
    echo Starting Tobi UI on http://localhost:3000 ...
    cd /d "%UI_DIR%"
    start /b npm run dev -- --hostname 0.0.0.0 --port 3000
    cd /d "%SCRIPT_DIR%"
    timeout /t 5 /nobreak >nul
)

:: Launch Tobi backend
echo Launching Tobi backend (%MODE%)...
python -m Tobi.main %MODE%

pause
