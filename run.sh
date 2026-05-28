#!/bin/bash

# Exit on error
set -e

# Navigate to the script's directory to ensure relative paths work
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "============================================="
echo "   Diffusion4Mac - Developer Launch Script   "
echo "============================================="

# Initialize pyenv if present to ensure the active python version (with torch/diffusers) is used
if [ -d "$HOME/.pyenv" ]; then
    echo "Initializing pyenv..."
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    if command -v pyenv >/dev/null 2>&1; then
        eval "$(pyenv init --path)"
        eval "$(pyenv init -)"
        echo "Using Python version: $(pyenv version-name)"
    fi
fi

# Print active python info for verification
echo "Active Python: $(which python) ($(python --version 2>&1))"

# Check node & npm
if ! command -v npm >/dev/null 2>&1; then
    echo "Error: npm is not installed or not in PATH."
    exit 1
fi

# Ensure node_modules are installed in electron_app
if [ ! -d "electron_app/node_modules" ]; then
    echo "Installing Electron app dependencies (node_modules)..."
    cd electron_app
    npm install
    cd ..
fi

# Start the Electron development server
echo "Launching Electron Dev Server..."
cd electron_app
npm run electron:serve
