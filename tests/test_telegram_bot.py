"""
Test Telegram Bot
Quick test to verify Telegram bot integration works
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from helpers.tools.telegram_clock_bot import TelegramClockBot

async def test_telegram_bot():
    """Test Telegram bot functionality"""
    print("📱 Testing Telegram Bot...")
    
    # Check credentials
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Missing Telegram credentials!")
        print("Please add to .env file:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token")
        print("TELEGRAM_CHAT_ID=your_chat_id")
        return False
    
    print(f"✅ Telegram credentials found")
    
    try:
        # Initialize bot
        bot = TelegramClockBot()
        
        # Send test message
        print("📤 Sending test message...")
        await bot.send_notification(
            "🧪 **Test Message**\n"
            "Telegram bot integration is working!\n"
            "🕐 Time: " + str(asyncio.get_event_loop().time())
        )
        
        print("✅ Test message sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

async def main():
    success = await test_telegram_bot()
    if success:
        print("\n🎉 Telegram bot test PASSED!")
    else:
        print("\n💥 Telegram bot test FAILED!")

if __name__ == "__main__":
    asyncio.run(main())
