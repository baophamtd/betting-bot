"""
Main Clock In/Out Bot
Automates Paylocity timekeeping with Telegram control and scheduling
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, time as dt_time
import schedule
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from helpers.tools.paylocity_client import PaylocityClient
from helpers.tools.telegram_clock_bot import TelegramClockBot

class ClockBot:
    def __init__(self):
        self.logger = self.setup_logging()
        self.paylocity_client = None
        self.telegram_bot = None
        self.is_running = False
        
        # Schedule times (can be configured via .env)
        self.clock_in_time = os.getenv('CLOCK_IN_TIME', '09:00')
        self.clock_out_time = os.getenv('CLOCK_OUT_TIME', '17:00')
        self.lunch_start_time = os.getenv('LUNCH_START_TIME', '12:00')
        self.lunch_end_time = os.getenv('LUNCH_END_TIME', '13:00')
        
        self.logger.info("🕐 Clock Bot initialized")

    def setup_logging(self):
        """Setup logging configuration"""
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/clock_bot.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    async def perform_clock_action(self, action_name: str, display_name: str):
        """Perform a clock action and send Telegram notification"""
        try:
            self.logger.info(f"🕐 Starting {display_name}...")
            
            # Initialize client if needed
            if not self.paylocity_client:
                self.paylocity_client = PaylocityClient(headless=True)
                if not self.paylocity_client.start():
                    error_msg = f"❌ Failed to start browser for {display_name}"
                    self.logger.error(error_msg)
                    await self.send_telegram_notification(error_msg)
                    return False

            # Login if needed
            if not self.paylocity_client.login():
                error_msg = f"❌ Failed to login to Paylocity for {display_name}"
                self.logger.error(error_msg)
                await self.send_telegram_notification(error_msg)
                return False

            # Perform the action
            action_method = getattr(self.paylocity_client, action_name)
            success = action_method()

            if success:
                success_msg = (
                    f"✅ **{display_name} Successful!**\n"
                    f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                self.logger.info(f"✅ {display_name} completed successfully")
                await self.send_telegram_notification(success_msg)
                return True
            else:
                error_msg = (
                    f"❌ **{display_name} Failed**\n"
                    f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"💡 The button might not be available or you're already in that state."
                )
                self.logger.warning(f"⚠️ {display_name} failed - button not available")
                await self.send_telegram_notification(error_msg)
                return False

        except Exception as e:
            error_msg = (
                f"❌ **{display_name} Error:** {str(e)}\n"
                f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.logger.error(f"❌ {display_name} error: {e}")
            await self.send_telegram_notification(error_msg)
            return False
        finally:
            # Clean up client
            if self.paylocity_client:
                self.paylocity_client.close()
                self.paylocity_client = None

    async def send_telegram_notification(self, message: str):
        """Send notification via Telegram"""
        try:
            if not self.telegram_bot:
                self.telegram_bot = TelegramClockBot()
            await self.telegram_bot.send_notification(message)
        except Exception as e:
            self.logger.error(f"❌ Failed to send Telegram notification: {e}")

    def scheduled_clock_in(self):
        """Scheduled clock in (runs in background thread)"""
        asyncio.run(self.perform_clock_action("clock_in", "Scheduled Clock In"))

    def scheduled_clock_out(self):
        """Scheduled clock out (runs in background thread)"""
        asyncio.run(self.perform_clock_action("clock_out", "Scheduled Clock Out"))

    def scheduled_lunch_start(self):
        """Scheduled lunch start (runs in background thread)"""
        asyncio.run(self.perform_clock_action("start_lunch", "Scheduled Lunch Start"))

    def scheduled_lunch_end(self):
        """Scheduled lunch end (runs in background thread)"""
        asyncio.run(self.perform_clock_action("end_lunch", "Scheduled Lunch End"))

    def setup_schedule(self):
        """Setup cron-like scheduling (DISABLED for manual control only)"""
        self.logger.info("📅 Scheduled tasks DISABLED - Manual control only")
        
        # Clear existing jobs
        schedule.clear()
        
        # SCHEDULING DISABLED - Only manual Telegram commands will work
        # Uncomment the lines below to enable automatic scheduling:
        
        # schedule.every().monday.at(self.clock_in_time).do(self.scheduled_clock_in)
        # schedule.every().tuesday.at(self.clock_in_time).do(self.scheduled_clock_in)
        # schedule.every().wednesday.at(self.clock_in_time).do(self.scheduled_clock_in)
        # schedule.every().thursday.at(self.clock_in_time).do(self.scheduled_clock_in)
        # schedule.every().friday.at(self.clock_in_time).do(self.scheduled_clock_in)
        
        # schedule.every().monday.at(self.clock_out_time).do(self.scheduled_clock_out)
        # schedule.every().tuesday.at(self.clock_out_time).do(self.scheduled_clock_out)
        # schedule.every().wednesday.at(self.clock_out_time).do(self.scheduled_clock_out)
        # schedule.every().thursday.at(self.clock_out_time).do(self.scheduled_clock_out)
        # schedule.every().friday.at(self.clock_out_time).do(self.scheduled_clock_out)
        
        # schedule.every().monday.at(self.lunch_start_time).do(self.scheduled_lunch_start)
        # schedule.every().tuesday.at(self.lunch_start_time).do(self.scheduled_lunch_start)
        # schedule.every().wednesday.at(self.lunch_start_time).do(self.scheduled_lunch_start)
        # schedule.every().thursday.at(self.lunch_start_time).do(self.scheduled_lunch_start)
        # schedule.every().friday.at(self.lunch_start_time).do(self.scheduled_lunch_start)
        
        # schedule.every().monday.at(self.lunch_end_time).do(self.scheduled_lunch_end)
        # schedule.every().tuesday.at(self.lunch_end_time).do(self.scheduled_lunch_end)
        # schedule.every().wednesday.at(self.lunch_end_time).do(self.scheduled_lunch_end)
        # schedule.every().thursday.at(self.lunch_end_time).do(self.scheduled_lunch_end)
        # schedule.every().friday.at(self.lunch_end_time).do(self.scheduled_lunch_end)
        
        self.logger.info(f"📅 Schedule DISABLED - Use Telegram commands:")
        self.logger.info(f"   /clockin - Clock in manually")
        self.logger.info(f"   /clockout - Clock out manually") 
        self.logger.info(f"   /lunchstart - Start lunch manually")
        self.logger.info(f"   /lunchend - End lunch manually")

    async def start_telegram_bot(self):
        """Start the Telegram bot for manual control"""
        try:
            self.telegram_bot = TelegramClockBot()
            self.logger.info("📱 Starting Telegram bot...")
            
            # Send startup notification
            await self.send_telegram_notification(
                "🚀 **Clock Bot Started!**\n"
                f"📅 **Scheduling DISABLED** - Manual control only\n\n"
                f"**Available Commands:**\n"
                f"• /clockin - Clock in manually\n"
                f"• /clockout - Clock out manually\n"
                f"• /lunchstart - Start lunch manually\n"
                f"• /lunchend - End lunch manually\n"
                f"• /status - Check current status\n"
                f"• /help - Show all commands\n\n"
                f"Use /help for more details!"
            )
            
            # Run Telegram bot (this will block)
            await self.telegram_bot.run_async()
            
        except Exception as e:
            self.logger.error(f"❌ Telegram bot error: {e}")

    async def run_scheduler(self):
        """Run the scheduler in background"""
        self.logger.info("⏰ Starting scheduler...")
        while self.is_running:
            schedule.run_pending()
            await asyncio.sleep(1)  # Check every second

    async def start(self):
        """Start the clock bot with both scheduling and Telegram control"""
        try:
            self.is_running = True
            self.setup_schedule()
            
            # Start both scheduler and Telegram bot concurrently
            await asyncio.gather(
                self.run_scheduler(),
                self.start_telegram_bot()
            )
            
        except KeyboardInterrupt:
            self.logger.info("🛑 Received interrupt signal")
        except Exception as e:
            self.logger.error(f"❌ Clock bot error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop the clock bot"""
        self.is_running = False
        self.logger.info("🛑 Clock bot stopped")

def main():
    """Main entry point"""
    clock_bot = ClockBot()
    asyncio.run(clock_bot.start())

if __name__ == "__main__":
    main()
