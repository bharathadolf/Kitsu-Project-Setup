@echo off
setlocal EnableDelayedExpansion

:: Configuration
set "REPO_URL=https://github.com/bharathadolf/Kitsu-Project-Setup.git"
set "INSTALL_DIR=%USERPROFILE%\kitsu-project-setup"
set "APP_WINDOW_TITLE=ProjectIngesterApp"
set "CHECK_INTERVAL=10"

echo ==========================================
echo    Kitsu Project - Auto-Updater Launcher
echo ==========================================

:: ---------------------------------------------------------
:: 1. Environment Check
:: ---------------------------------------------------------
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed. Please install Git and try again.
    pause
    exit /b 1
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python and try again.
    pause
    exit /b 1
)
set "PYTHON_CMD=python"

:: ---------------------------------------------------------
:: 2. Initial Setup / Update
:: ---------------------------------------------------------
if not exist "%INSTALL_DIR%" (
    echo [INFO] First time setup. Cloning repository...
    git clone "%REPO_URL%" "%INSTALL_DIR%"
)

cd /d "%INSTALL_DIR%"

:START_APP
:: Ensure we are on main branch and clean
git checkout main >nul 2>&1
git pull origin main >nul 2>&1

:: Install dependencies (quietly)
echo [INFO] Checking dependencies...
"%PYTHON_CMD%" -m pip install -r requirements.txt >nul 2>&1

:: Launch App in background
echo [INFO] Launching Application...
start "%APP_WINDOW_TITLE%" "%PYTHON_CMD%" main.py

:: ---------------------------------------------------------
:: 3. Monitor Loop
:: ---------------------------------------------------------
:MONITOR_LOOP
timeout /t %CHECK_INTERVAL% /nobreak >nul

:: Fetch updates from remote
git fetch origin main >nul 2>&1

:: Get local and remote hashes
for /f %%i in ('git rev-parse HEAD') do set LOCAL_HASH=%%i
for /f %%i in ('git rev-parse origin/main') do set REMOTE_HASH=%%i

if "%LOCAL_HASH%" neq "%REMOTE_HASH%" (
    echo.
    echo [UPDATE DETECTED] Remote hash: %REMOTE_HASH%
    echo [ACTION] Closing application and updating...
    
    :: Kill the specific application
    :: Note: Since we don't have the PID easily, we rely on taskkill by window title 
    :: or simply killing python processes launched from this folder could be tricky.
    :: For now, we try to kill strictly by Window Title if main.py sets it, 
    :: OR we might have to just kill all python.exe processes (dangerous).
    :: Refined approach: We will assume main.py sets title via code or we just restart.
    
    taskkill /FI "WINDOWTITLE eq %APP_WINDOW_TITLE%*" /T /F >nul 2>&1
    
    :: Force update
    git reset --hard origin/main
    git clean -fd
    
    echo [INFO] Update complete. Restarting...
    goto START_APP
)

goto MONITOR_LOOP
