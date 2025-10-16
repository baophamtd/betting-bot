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
        self.token = os.getenv('BAO_TELEGRAM_TOKEN')
        self.chat_id = os.getenv('BAO_TELEGRAM_ID')
        self.paylocity_client = None
        self.logger = logging.getLogger(__name__)
        
        if not self.token or not self.chat_id:
            self.logger.error("❌ Missing Telegram credentials in .env file")
            raise ValueError("Missing BAO_TELEGRAM_TOKEN or BAO_TELEGRAM_ID")
            
        self.application = Application.builder().token(self.token).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Setup Telegram command handlers"""
        # Command handlers
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
        welcome_message = """
🕐 **Paylocity Clock Bot** 🕐

Welcome! I can help you automate your clock in/out on Paylocity.

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
        await update.message.reply_text("🕐 Starting clock in process...")
        await self.perform_clock_action(update, "clock_in", "Clock In")

    async def clock_out_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clockout command"""
        await update.message.reply_text("🕕 Starting clock out process...")
        await self.perform_clock_action(update, "clock_out", "Clock Out")

    async def lunch_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /lunchstart command"""
        await update.message.reply_text("🍽️ Starting lunch break...")
        await self.perform_clock_action(update, "start_lunch", "Start Lunch")

    async def lunch_end_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /lunchend command"""
        await update.message.reply_text("🍽️ Ending lunch break...")
        await self.perform_clock_action(update, "end_lunch", "End Lunch")

    async def skip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /skip command"""
        await update.message.reply_text("🔄 Clicking 'Skip for Now' button...")
        await self.perform_clock_action(update, "handle_skip_for_now", "Skip for Now")

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

    async def perform_clock_action(self, update: Update, action_name: str, display_name: str):
        """Perform a clock action and send result"""
        try:
            if not self.paylocity_client:
                self.paylocity_client = PaylocityClient(headless=True)
                if not self.paylocity_client.start():
                    await update.message.reply_text(f"❌ Failed to start browser for {display_name}")
                    return
            
            if not self.paylocity_client.login():
                await update.message.reply_text(f"❌ Failed to login to Paylocity for {display_name}")
                return
                
            # Perform the action
            action_method = getattr(self.paylocity_client, action_name)
            success = action_method()
            
            if success:
                await update.message.reply_text(
                    f"✅ **{display_name} Successful!**\n"
                    f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                await update.message.reply_text(
                    f"❌ **{display_name} Failed**\n"
                    f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"💡 The button might not be available or you're already in that state."
                )
                
        except Exception as e:
            await update.message.reply_text(
                f"❌ **{display_name} Error:** {str(e)}\n"
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
        """Send notification to configured chat"""
        try:
            bot = Bot(token=self.token)
            await bot.send_message(chat_id=self.chat_id, text=message, parse_mode='Markdown')
        except Exception as e:
            self.logger.error(f"❌ Failed to send notification: {e}")

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
