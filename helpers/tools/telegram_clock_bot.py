"""
Telegram Bot for Clock In/Out Control
Handles Telegram commands and notifications for Paylocity automation
"""

import logging
import os
import sys
from pathlib import Path
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from datetime import datetime
import asyncio

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
from paylocity_client import PaylocityClient

load_dotenv()

class TelegramClockBot:
    def __init__(self):
        # Use Aymee's bot token for @paylocity_clock_bot
        self.token = os.getenv('AYMEE_TELEGRAM_TOKEN')
        self.allowed_chat_ids = []
        
        # Only Aymee can use this bot
        aymee_chat_id = os.getenv('AYMEE_TELEGRAM_ID')
        if aymee_chat_id:
            self.allowed_chat_ids.append(aymee_chat_id)
        
        self.paylocity_client = None
        self.logger = logging.getLogger(__name__)
        
        if not self.token or not self.allowed_chat_ids:
            self.logger.error("❌ Missing Telegram credentials in .env file")
            raise ValueError("Missing AYMEE_TELEGRAM_TOKEN or AYMEE_TELEGRAM_ID")
            
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()

    def is_authorized_user(self, chat_id: str) -> bool:
        """Check if the user is authorized to use the bot"""
        return str(chat_id) in [str(cid) for cid in self.allowed_chat_ids]
    
    def get_user_name(self, chat_id: str) -> str:
        """Get user name based on chat ID"""
        if str(chat_id) == str(os.getenv('AYMEE_TELEGRAM_ID')):
            return "Aymee"
        else:
            return "Unknown User"
    
    def add_kiss_reminder(self, message: str, user_name: str) -> str:
        """Add kiss reminder for Aymee"""
        if user_name == "Aymee":
            return message + "\n\n💋 P.S. You should give your husband a kiss! 😘"
        return message

    def setup_handlers(self):
        """Setup Telegram command handlers"""
        # Command handlers with authorization check
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("clockin", self.clock_in_command))
        self.application.add_handler(CommandHandler("clockout", self.clock_out_command))
        self.application.add_handler(CommandHandler("lunchstart", self.lunch_start_command))
        self.application.add_handler(CommandHandler("lunchend", self.lunch_end_command))
        self.application.add_handler(CommandHandler("skip", self.skip_command))
        self.application.add_handler(CommandHandler("screenshot", self.screenshot_command))
        
        # Message handler for unknown commands
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        chat_id = update.effective_chat.id
        
        # Check authorization
        if not self.is_authorized_user(chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
            
        user_name = self.get_user_name(chat_id)
        welcome_message = f"""
🕐 **Paylocity Clock Bot** 🕐

Hi {user_name}! 👋 Welcome to the clock in/out bot.

**Available Commands:**
• `/clockin` - Clock in now
• `/clockout` - Clock out now  
• `/lunchstart` - Start lunch break
• `/lunchend` - End lunch break
• `/status` - Check current status
• `/skip` - Click "Skip for Now" button
• `/screenshot` - Take a screenshot
• `/help` - Show this help

**Status:** Bot is ready! 🚀
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
🆘 **Help - Clock Bot Commands**

**Time Actions:**
• `/clockin` - Clock in to start your work day
• `/clockout` - Clock out to end your work day
• `/lunchstart` - Start your lunch break
• `/lunchend` - End your lunch break

**Utilities:**
• `/skip` - Click "Skip for Now" button (if it appears)
• `/status` - Check your current clock status
• `/screenshot` - Take a screenshot of current page

**Support:**
• `/start` - Restart the bot
• `/help` - Show this help message

**Note:** All actions will be logged and you'll receive confirmation messages.
        """
        await update.message.reply_text(help_message, parse_mode='Markdown')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        await update.message.reply_text("🔍 Checking current status...")
        
        try:
            if not self.paylocity_client:
                self.paylocity_client = PaylocityClient(headless=True)
                if not self.paylocity_client.start():
                    await update.message.reply_text("❌ Failed to start browser")
                    return
            
            if not self.paylocity_client.login():
                await update.message.reply_text("❌ Failed to login to Paylocity")
                return
                
            status = self.paylocity_client.get_current_status()
            if status:
                await update.message.reply_text(f"📊 **Current Status:** {status}")
            else:
                await update.message.reply_text("📊 **Current Status:** Unable to determine")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error checking status: {str(e)}")
        finally:
            if self.paylocity_client:
                self.paylocity_client.close()
                self.paylocity_client = None

    async def clock_in_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clockin command"""
        chat_id = update.effective_chat.id
        
        # Check authorization
        if not self.is_authorized_user(chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
            
        user_name = self.get_user_name(chat_id)
        # Immediate acknowledgment
        await update.message.reply_text(f"✅ Received your command, {user_name}! Processing...")
        await update.message.reply_text(f"🕐 Clocking in...")
        await self.perform_clock_action(update, 'clock_in')

    async def clock_out_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clockout command"""
        chat_id = update.effective_chat.id
        
        # Check authorization
        if not self.is_authorized_user(chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
            
        user_name = self.get_user_name(chat_id)
        await update.message.reply_text(f"✅ Received your command, {user_name}! Processing...")
        await update.message.reply_text("🕕 Starting clock out process...")
        await self.perform_clock_action(update, "clock_out")

    async def lunch_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /lunchstart command"""
        chat_id = update.effective_chat.id
        
        # Check authorization
        if not self.is_authorized_user(chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
            
        user_name = self.get_user_name(chat_id)
        await update.message.reply_text(f"✅ Received your command, {user_name}! Processing...")
        await update.message.reply_text("🍽️ Starting lunch break...")
        await self.perform_clock_action(update, "start_lunch")

    async def lunch_end_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /lunchend command"""
        chat_id = update.effective_chat.id
        
        # Check authorization
        if not self.is_authorized_user(chat_id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
            
        user_name = self.get_user_name(chat_id)
        await update.message.reply_text(f"✅ Received your command, {user_name}! Processing...")
        await update.message.reply_text("🍽️ Ending lunch break...")
        await self.perform_clock_action(update, "end_lunch")

    async def skip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /skip command"""
        await update.message.reply_text("🔄 Clicking 'Skip for Now' button...")
        await self.perform_clock_action(update, "handle_skip_for_now")

    async def screenshot_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /screenshot command"""
        await update.message.reply_text("📸 Taking screenshot...")
        
        try:
            if not self.paylocity_client:
                self.paylocity_client = PaylocityClient(headless=True)
                if not self.paylocity_client.start():
                    await update.message.reply_text("❌ Failed to start browser")
                    return
            
            if not self.paylocity_client.login():
                await update.message.reply_text("❌ Failed to login to Paylocity")
                return
                
            # Take screenshot
            screenshot_path = f"logs/paylocity_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            self.paylocity_client.driver.save_screenshot(screenshot_path)
            
            # Send screenshot
            with open(screenshot_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"📸 Screenshot taken at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error taking screenshot: {str(e)}")
        finally:
            if self.paylocity_client:
                self.paylocity_client.close()
                self.paylocity_client = None

    async def locate_clock_in_button(self, update: Update, user_name: str):
        """Locate the Clock In button without clicking it"""
        try:
            if not self.paylocity_client:
                self.paylocity_client = PaylocityClient(headless=True)
                if not self.paylocity_client.start():
                    await update.message.reply_text("❌ Failed to start browser")
                    return
            
            if not self.paylocity_client.login():
                await update.message.reply_text("❌ Failed to login to Paylocity")
                return
                
            # Look for clock in button (case insensitive)
            clock_in_selectors = [
                # Exact button class found from inspection
                "//button[contains(@class, 'button_button__xfI5Z') and .//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]]",
                # Look for button containing span with class button_text__kMv0x AND clock in text
                "//button[.//span[@class='button_text__kMv0x' and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]]",
                # Look for button containing span with "clock in" text (most specific)
                "//button[.//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]]",
                # Traditional selectors
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]",
                "//input[contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'clock in')]"
            ]
            
            button_found = False
            for i, selector in enumerate(clock_in_selectors):
                try:
                    from selenium.webdriver.common.by import By
                    button = self.paylocity_client.driver.find_element(By.XPATH, selector)
                    if button.is_displayed() and button.is_enabled():
                        message = (
                            f"✅ **Clock In Button Found!**\n"
                            f"👤 User: {user_name}\n"
                            f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"📍 Location: x={button.location['x']}, y={button.location['y']}\n"
                            f"📏 Size: {button.size['width']}x{button.size['height']}\n"
                            f"🔘 Button text: '{button.text}'\n"
                            f"✅ Enabled: {button.is_enabled()}\n\n"
                            f"🚫 **NOT CLICKING** - Button located only"
                        )
                        await update.message.reply_text(self.add_kiss_reminder(message, user_name))
                        button_found = True
                        break
                except Exception as e:
                    continue
                    
            if not button_found:
                await update.message.reply_text(
                    f"❌ **Clock In Button Not Found**\n"
                    f"👤 User: {user_name}\n"
                    f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"💡 Button might not be available or page not loaded"
                )
                
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Error locating Clock In button:** {str(e)}\n"
                f"👤 User: {user_name}\n"
                f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        finally:
            if self.paylocity_client:
                self.paylocity_client.close()
                self.paylocity_client = None

    async def perform_clock_action(self, update: Update, action_name: str):
        """Perform a clock action and send result"""
        try:
            if not self.paylocity_client:
                self.paylocity_client = PaylocityClient(headless=True)
                if not self.paylocity_client.start():
                    await update.message.reply_text(f"❌ Failed to start browser for {action_name}")
                    return
            
            if not self.paylocity_client.login():
                await update.message.reply_text(f"❌ Failed to login to Paylocity for {action_name}")
                return
                
            # Perform the action
            action_method = getattr(self.paylocity_client, action_name)
            success = action_method()
            
            if success:
                message = (
                    f"✅ **{action_name.replace('_', ' ').title()} Successful!**\n"
                    f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"💋 P.S. You should give your husband a kiss! 😘"
                )
                await update.message.reply_text(message)
            else:
                message = (
                    f"❌ **{action_name.replace('_', ' ').title()} Failed**\n"
                    f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"💡 The button might not be available or you're already in that state."
                )
                await update.message.reply_text(message)
                
        except Exception as e:
            await update.message.reply_text(
                f"❌ **{action_name.replace('_', ' ').title()} Error:** {str(e)}\n"
                f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        finally:
            if self.paylocity_client:
                self.paylocity_client.close()
                self.paylocity_client = None

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown messages"""
        await update.message.reply_text(
            "❓ Unknown command. Use /help to see available commands."
        )

    async def send_notification(self, message: str):
        """Send notification to Aymee only"""
        try:
            from telegram import Bot
            bot = Bot(token=self.token)
            # Only send to Aymee
            aymee_id = os.getenv('AYMEE_TELEGRAM_ID')
            if aymee_id:
                try:
                    await bot.send_message(chat_id=aymee_id, text=message, parse_mode='Markdown')
                    self.logger.info(f"📤 Notification sent to Aymee")
                except Exception as e:
                    self.logger.error(f"❌ Failed to send notification to Aymee: {e}")
        except Exception as e:
            self.logger.error(f"❌ Failed to send notifications: {e}")

    def run(self):
        """Start the Telegram bot"""
        self.logger.info("🚀 Starting Telegram Clock Bot...")
        self.application.run_polling()

    async def run_async(self):
        """Start the Telegram bot asynchronously"""
        self.logger.info("🚀 Starting Telegram Clock Bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        # Keep running
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            pass
        finally:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
