#!/bin/bash
# Setup script for Vault RPG

# Exit immediately if a command exits with a non-zero status
set -e

echo "=== Vault RPG Setup Script ==="

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment without pip (to support minimal systems like Debian/Ubuntu)
echo "Creating virtual environment in .venv (without pip)..."
python3 -m venv .venv --without-pip

# Bootstrap pip inside the virtual environment
echo "Bootstrapping pip inside .venv..."
if ! curl -sS https://bootstrap.pypa.io/get-pip.py | .venv/bin/python3; then
    echo "Error: Failed to download and install pip. Please check your internet connection."
    exit 1
fi

# Install requirements using the bootstrapped pip
echo "Installing dependencies from requirements.txt..."
.venv/bin/python3 -m pip install -r requirements.txt

echo "Setup complete! You can run the game using ./run.sh"
