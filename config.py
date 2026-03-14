"""Configuration for gold price tracker."""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1251073256")

# Gold API - Get free key at https://www.goldapi.io
GOLDAPI_KEY = os.getenv("GOLDAPI_KEY", "YOUR_GOLDAPI_KEY_HERE")

# Price thresholds (USD per ounce)
ALERT_PRICE_ABOVE = float(os.getenv("ALERT_PRICE_ABOVE", "0"))  # 0 = disabled
ALERT_PRICE_BELOW = float(os.getenv("ALERT_PRICE_BELOW", "0"))  # 0 = disabled

# Update interval (minutes)
UPDATE_INTERVAL_MINUTES = int(os.getenv("UPDATE_INTERVAL_MINUTES", "15"))

# Logging
LOG_FILE = "gold_tracker.log"
