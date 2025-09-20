#!/bin/bash

# AppIdeas Bot Cron Script
# Run daily at 8 PM (20:00)

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source betting-bot-env/bin/activate

# Run the AppIdeas bot
python bots/appideas_bot.py

# Deactivate virtual environment
deactivate
