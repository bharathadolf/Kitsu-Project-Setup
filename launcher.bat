@echo off
setlocal

:: Configuration
set "REPO_URL=https://github.com/bharathadolf/Kitsu-Project-Setup.git"
set "INSTALL_DIR=%USERPROFILE%\kitsu-project-setup"

echo ==========================================
echo    Kitsu Project Setup - Launcher
echo ==========================================

:: Check for Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed. Please install Git and try again.
    pause
    exit /b 1
)

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python and try again.
    pause
    exit /b 1
)
set "PYTHON_CMD=python"

:: Setup Directory
if exist "%INSTALL_DIR%" (
    echo [INFO] Updating existing installation...
    cd /d "%INSTALL_DIR%"
    git pull
) else (
    echo [INFO] Cloning repository...
    git clone "%REPO_URL%" "%INSTALL_DIR%"
    cd /d "%INSTALL_DIR%"
)

:: Install Dependencies
echo [INFO] Installing requirements...
"%PYTHON_CMD%" -m pip install -r requirements.txt

:: Run Application
echo [INFO] Starting application...
"%PYTHON_CMD%" main.py

endlocal
