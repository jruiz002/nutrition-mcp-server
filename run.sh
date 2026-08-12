#!/bin/bash

# Exit on error
set -e

echo "Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

# Run the chatbot
echo "Starting Chatbot Host..."
python3 src/client/chatbot.py
