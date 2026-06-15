#!/bin/bash
# Run script for Vault RPG

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Running setup..."
    bash setup.sh
fi

# Check if Ollama is running
echo "Checking Ollama status..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Ollama is running. Dynamic NPCs active!"
else
    echo "WARNING: Ollama service is not running on http://localhost:11434."
    echo "The game will automatically fall back to rule-based dialog mode."
    echo "To get dynamic LLM responses, make sure Ollama is running and has 'llama3.2' installed."
fi

# Run the game
echo "Starting Vault RPG..."
.venv/bin/python3 main.py
