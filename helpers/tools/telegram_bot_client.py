import telepot
import pickle
from dotenv import load_dotenv
import os

class TelegramBotClient:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Set up IDs for Telegram
        self.bao_id = os.getenv('BAO_TELEGRAM_ID')
        self.bot_token = os.getenv('BAO_TELEGRAM_TOKEN')

        if not self.bao_id or not self.bot_token:
            raise ValueError("BAO_TELEGRAM_ID or BAO_TELEGRAM_TOKEN not found in environment variables")

        # Create a bot
        self.bot = telepot.Bot(self.bot_token)

    def send_message(self, message):
        """
        Send a message using the Telegram bot.

        :param message: The message to send
        """
        try:
            self.bot.sendMessage(self.bao_id, message)
            print(f"Message sent: {message}")
        except Exception as e:
            print(f"Failed to send message: {e}")