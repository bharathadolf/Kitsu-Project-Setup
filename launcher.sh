#!/bin/bash

# Configuration
REPO_URL="https://github.com/bharathadolf/Kitsu-Project-Setup.git"
INSTALL_DIR="$HOME/kitsu-project-setup"

echo "=========================================="
echo "   Kitsu Project Setup - Launcher"
echo "=========================================="

# Check for Git
if ! command -v git &> /dev/null; then
    echo "[ERROR] Git is not installed. Please install Git and try again."
    exit 1
fi

# Check for Python
if command -v python &> /dev/null; then
    PYTHON_CMD=python
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    echo "[ERROR] Python is not installed. Please install Python and try again."
    exit 1
fi

# Setup Directory
if [ -d "$INSTALL_DIR" ]; then
    echo "[INFO] Updating existing installation..."
    cd "$INSTALL_DIR" || exit
    git pull
else
    echo "[INFO] Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR" || exit
fi

# Install Dependencies
echo "[INFO] Installing requirements..."
"$PYTHON_CMD" -m pip install -r requirements.txt

# Run Application
echo "[INFO] Starting application..."
"$PYTHON_CMD" main.py
