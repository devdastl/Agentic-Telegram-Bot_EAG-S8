import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("telegram.env")

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Other configuration settings
MAX_MESSAGE_LENGTH = 4096  # Telegram's max message length
ALLOWED_USERS = os.getenv('ALLOWED_USERS', '').split(',')  # List of allowed user IDs 