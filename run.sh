#!/bin/bash

# Exit on error
set -e

# Navigate to the script's directory to ensure relative paths work
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Prioritize local native Node.js if available
if [ -d "$DIR/node-native/bin" ]; then
    echo "Prioritizing local native Node.js in node-native/bin..."
    export PATH="$DIR/node-native/bin:$PATH"
fi

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

# Setup Python virtual environment
if [ -d "venv" ] && [ "$(uname)" == "Darwin" ] && [ "$(uname -m)" == "arm64" ]; then
    if file venv/bin/python3 | grep -q "x86_64"; then
        echo "============================================="
        echo "WARNING: Your virtual environment (venv) was built for Intel (x86_64)"
        echo "but your Mac is Apple Silicon (arm64)."
        echo "This causes PyTorch MPS acceleration to run extremely slowly under Rosetta 2."
        echo "Recreating virtual environment natively..."
        echo "============================================="
        rm -rf venv
    fi
fi

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment (venv)..."
    if [ "$(uname)" == "Darwin" ] && [ "$(uname -m)" == "arm64" ]; then
        echo "Using system universal python3 to create native arm64 virtual environment..."
        /usr/bin/python3 -m venv venv
    else
        python3 -m venv venv
    fi
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo "Installing Python dependencies (requirements.txt)..."
    pip install --upgrade pip
    pip install -r backends/stable_diffusion/requirements.txt
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Print active python info for verification
echo "Active Python: $(which python3) ($(python3 --version 2>&1))"

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
export ELECTRON_ENABLE_LOGGING=1
npm run electron:serve
