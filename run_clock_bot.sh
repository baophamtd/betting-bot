#!/bin/bash

# Clock Bot Runner Script
# Starts the clock in/out bot with proper environment

echo "🕐 Starting Clock Bot..."

# Check if virtual environment exists
if [ ! -d "betting-bot-env" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv betting-bot-env"
    exit 1
fi

# Activate virtual environment
source betting-bot-env/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please copy env.example to .env and configure your credentials"
    exit 1
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -q python-telegram-bot schedule

# Create logs directory
mkdir -p logs

# Start the clock bot
echo "🚀 Starting Clock Bot..."
python bots/clock_bot.py
