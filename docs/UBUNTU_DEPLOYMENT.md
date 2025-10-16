# 🐧 Ubuntu Server Deployment Guide

Complete guide to deploy and run the Clock Bot on Ubuntu server.

## 📋 **Prerequisites**

- Ubuntu 20.04 or later
- Git installed
- Python 3.8+
- sudo access

---

## 🚀 **Step-by-Step Deployment**

### **1. Install System Dependencies**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Install Chrome dependencies
sudo apt install -y wget gnupg2 software-properties-common apt-transport-https ca-certificates

# Install Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install -y

# Verify Chrome installation
google-chrome --version

# Install additional dependencies for headless Chrome
sudo apt install -y xvfb libxi6 libgconf-2-4 libnss3 libxss1 libappindicator3-1 libcurl4
```

### **2. Clone Repository**

```bash
# Clone the repository
cd ~
git clone <your-repo-url> betting-bot
cd betting-bot

# Checkout the clock bot branch
git checkout clock-in-bot
```

### **3. Setup Python Virtual Environment**

```bash
# Create virtual environment
python3 -m venv betting-bot-env

# Activate virtual environment
source betting-bot-env/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install python-telegram-bot schedule selenium undetected-chromedriver python-dotenv
```

### **4. Configure Environment Variables**

```bash
# Copy environment template
cp env.example .env

# Edit with your credentials
nano .env
```

Add your credentials:
```bash
# Paylocity credentials
PAYLOCITY_COMPANY_ID=301469
PAYLOCITY_USERNAME=your_paylocity_username
PAYLOCITY_PASSWORD=your_paylocity_password

# Telegram Bot credentials
BAO_TELEGRAM_TOKEN=your_telegram_bot_token
BAO_TELEGRAM_ID=your_telegram_chat_id

# Aymee's Telegram credentials
AYMEE_TELEGRAM_ID=aymee_chat_id_here

# Clock Bot Schedule (optional, currently disabled)
CLOCK_IN_TIME=09:00
CLOCK_OUT_TIME=17:00
LUNCH_START_TIME=12:00
LUNCH_END_TIME=13:00
```

Save and exit (Ctrl+O, Enter, Ctrl+X)

### **5. Test the Bot**

```bash
# Make sure you're in the virtual environment
source betting-bot-env/bin/activate

# Make startup script executable
chmod +x run_clock_bot.sh

# Test run (will run in foreground)
./run_clock_bot.sh
```

You should receive a startup message in Telegram. Press `Ctrl+C` to stop.

---

## 🔧 **Running as a System Service (Recommended)**

### **1. Create Systemd Service File**

```bash
sudo nano /etc/systemd/system/clock-bot.service
```

Add this content (replace `YOUR_USERNAME` and paths):

```ini
[Unit]
Description=Paylocity Clock In/Out Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/betting-bot
Environment="PATH=/home/YOUR_USERNAME/betting-bot/betting-bot-env/bin"
ExecStart=/home/YOUR_USERNAME/betting-bot/betting-bot-env/bin/python /home/YOUR_USERNAME/betting-bot/bots/clock_bot.py
Restart=always
RestartSec=10
StandardOutput=append:/home/YOUR_USERNAME/betting-bot/logs/clock_bot.log
StandardError=append:/home/YOUR_USERNAME/betting-bot/logs/clock_bot_error.log

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+O, Enter, Ctrl+X)

### **2. Enable and Start Service**

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable clock-bot

# Start the service
sudo systemctl start clock-bot

# Check status
sudo systemctl status clock-bot
```

### **3. Service Management Commands**

```bash
# Check if service is running
sudo systemctl status clock-bot

# View live logs
sudo journalctl -u clock-bot -f

# View recent logs
sudo journalctl -u clock-bot -n 100

# Restart service
sudo systemctl restart clock-bot

# Stop service
sudo systemctl stop clock-bot

# Disable service from starting on boot
sudo systemctl disable clock-bot
```

---

## 📊 **Monitoring and Logs**

### **View Application Logs**

```bash
# Real-time logs
tail -f ~/betting-bot/logs/clock_bot.log

# Error logs
tail -f ~/betting-bot/logs/clock_bot_error.log

# System service logs
sudo journalctl -u clock-bot -f
```

### **Check Bot Status**

```bash
# Check if process is running
ps aux | grep clock_bot

# Check service status
sudo systemctl status clock-bot

# Send /status command via Telegram
```

---

## 🔄 **Updating the Bot**

When you push new changes:

```bash
# SSH into your Ubuntu server
ssh user@your-server

# Navigate to project directory
cd ~/betting-bot

# Pull latest changes
git pull origin clock-in-bot

# Activate virtual environment
source betting-bot-env/bin/activate

# Update dependencies if needed
pip install --upgrade python-telegram-bot schedule selenium undetected-chromedriver

# Restart the service
sudo systemctl restart clock-bot

# Check logs to verify update
sudo journalctl -u clock-bot -n 50
```

---

## 🛡️ **Security Best Practices**

### **1. Secure Your .env File**

```bash
# Ensure .env is only readable by you
chmod 600 ~/.betting-bot/.env

# Verify permissions
ls -la ~/.betting-bot/.env
# Should show: -rw------- (600)
```

### **2. Setup Firewall (Optional)**

```bash
# Allow SSH
sudo ufw allow ssh

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### **3. Keep System Updated**

```bash
# Regular updates
sudo apt update && sudo apt upgrade -y

# Auto-security updates (optional)
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 🐛 **Troubleshooting**

### **Bot Won't Start**

```bash
# Check service status
sudo systemctl status clock-bot

# View error logs
sudo journalctl -u clock-bot -n 100

# Test manually
cd ~/betting-bot
source betting-bot-env/bin/activate
python bots/clock_bot.py
```

### **Chrome/ChromeDriver Issues**

```bash
# Check Chrome version
google-chrome --version

# Reinstall Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install -y

# Clear Chrome cache
rm -rf ~/.cache/selenium
```

### **Paylocity Login Fails**

- Check credentials in `.env` file
- Verify company ID is correct (301469)
- Check if Paylocity blocks server IPs (may need VPN)
- Test login manually on the server

### **Telegram Bot Not Responding**

```bash
# Check if bot token is correct
cat .env | grep BAO_TELEGRAM_TOKEN

# Verify chat IDs are correct
cat .env | grep TELEGRAM_ID

# Test Telegram connectivity
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

### **Permission Errors**

```bash
# Fix log directory permissions
mkdir -p ~/betting-bot/logs
chmod 755 ~/betting-bot/logs

# Fix service file ownership
sudo chown YOUR_USERNAME:YOUR_USERNAME /etc/systemd/system/clock-bot.service
```

---

## 📱 **Using the Bot**

Once deployed and running:

1. **Start Conversation**: Send `/start` to your bot
2. **Test Button Detection**: Send `/clockin` (won't click, just locates button)
3. **Check Status**: Send `/status`
4. **Get Help**: Send `/help`

Both you and Aymee can control the bot using the same commands!

---

## 🔄 **Auto-Restart on Server Reboot**

The systemd service is configured to start automatically on reboot. To verify:

```bash
# Check if service is enabled
sudo systemctl is-enabled clock-bot

# Should return: enabled
```

If not enabled:
```bash
sudo systemctl enable clock-bot
```

---

## 📞 **Support**

If you encounter issues:

1. Check logs: `sudo journalctl -u clock-bot -n 100`
2. Test manually: `python bots/clock_bot.py`
3. Verify credentials in `.env`
4. Check Chrome installation: `google-chrome --version`
5. Ensure virtual environment is activated

---

## 🎉 **Success!**

Your Clock Bot is now running 24/7 on Ubuntu server! Both you and Aymee can control it via Telegram commands anytime. 🚀
