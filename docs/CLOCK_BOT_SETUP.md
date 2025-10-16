# 🕐 Clock In/Out Bot Setup Guide

Automated Paylocity timekeeping with Telegram control and scheduling.

## 📋 Features

- **Automated Clock Actions**: Clock in, clock out, lunch start/end
- **Telegram Control**: Manual commands via Telegram bot
- **Scheduled Automation**: Automatic actions at configured times
- **Notifications**: Telegram notifications for all actions
- **Headless Operation**: Runs on Ubuntu server without display

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
# Activate virtual environment
source betting-bot-env/bin/activate

# Install new dependencies
pip install python-telegram-bot schedule
```

### 2. Configure Environment

Copy and edit the environment file:

```bash
cp env.example .env
```

Edit `.env` with your credentials:

```bash
# Paylocity credentials
PAYLOCITY_COMPANY_ID=your_company_id
PAYLOCITY_USERNAME=your_paylocity_username
PAYLOCITY_PASSWORD=your_password

# Telegram Bot credentials (using existing BAO credentials)
BAO_TELEGRAM_TOKEN=your_bot_token
BAO_TELEGRAM_ID=your_chat_id

# Schedule times (24-hour format)
CLOCK_IN_TIME=09:00
CLOCK_OUT_TIME=17:00
LUNCH_START_TIME=12:00
LUNCH_END_TIME=13:00
```

### 3. Create Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow instructions
3. Get your bot token
4. Start a chat with your bot and send `/start`
5. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)

### 4. Test Individual Components

```bash
# Test Paylocity login
python tests/test_paylocity_login.py

# Test Telegram bot
python tests/test_telegram_bot.py
```

### 5. Run the Clock Bot

```bash
# Start the full bot with Telegram control and scheduling
python bots/clock_bot.py
```

## 📱 Telegram Commands

Once running, you can control the bot via Telegram:

- `/start` - Welcome message and help
- `/help` - Show all available commands
- `/clockin` - Clock in now
- `/clockout` - Clock out now
- `/lunchstart` - Start lunch break
- `/lunchend` - End lunch break
- `/status` - Check current status
- `/screenshot` - Take screenshot

## ⏰ Scheduled Actions

The bot operates in **manual mode** by default - no automatic scheduling:

- **Manual Commands**: Use Telegram commands to control clock actions
- **No Cron Jobs**: Scheduling is disabled to prevent accidental clock ins
- **Safe Operation**: Only responds to explicit Telegram commands

### **Optional: Automatic Scheduling**
To enable automatic scheduling, uncomment the schedule lines in `bots/clock_bot.py`:

- **Clock In**: 9:00 AM (Monday-Friday)
- **Clock Out**: 5:00 PM (Monday-Friday)
- **Lunch Start**: 12:00 PM (Monday-Friday)
- **Lunch End**: 1:00 PM (Monday-Friday)

## 🐧 Ubuntu Server Deployment

### 1. Install Chrome and Dependencies

```bash
# Update system
sudo apt update

# Install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Install Python dependencies
sudo apt install -y python3-pip python3-venv
```

### 2. Setup Virtual Environment

```bash
# Create and activate venv
python3 -m venv clock-bot-env
source clock-bot-env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run as Service

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/clock-bot.service
```

Add this content:

```ini
[Unit]
Description=Clock In/Out Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/betting-bot
Environment=PATH=/path/to/betting-bot/clock-bot-env/bin
ExecStart=/path/to/betting-bot/clock-bot-env/bin/python bots/clock_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable clock-bot
sudo systemctl start clock-bot
sudo systemctl status clock-bot
```

## 🔧 Troubleshooting

### Common Issues

1. **Login Fails**: Check credentials and network connection
2. **Telegram Not Working**: Verify bot token and chat ID
3. **Chrome Issues**: Ensure Chrome is installed and updated
4. **Permission Errors**: Check file permissions and user access

### Logs

Check logs for debugging:

```bash
# Application logs
tail -f logs/clock_bot.log

# System service logs
sudo journalctl -u clock-bot -f
```

### Manual Testing

```bash
# Test individual components
python tests/test_paylocity_login.py
python tests/test_telegram_bot.py

# Run bot in foreground for debugging
python bots/clock_bot.py
```

## 🔒 Security Notes

- Keep `.env` file secure and never commit to git
- Use strong passwords for Paylocity
- Regularly rotate Telegram bot tokens
- Monitor logs for unauthorized access

## 📞 Support

If you encounter issues:

1. Check the logs first
2. Test individual components
3. Verify credentials and network
4. Check system resources (memory, disk space)

The bot is designed to be robust and handle common errors gracefully with Telegram notifications.
