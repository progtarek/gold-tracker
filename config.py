"""Configuration for gold price tracker."""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1251073256")

# Twelve Data API - Get free key at https://twelvedata.com/pricing (800 requests/day free tier)
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "YOUR_TWELVE_DATA_API_KEY_HERE")

# Price thresholds (USD per ounce)
ALERT_PRICE_ABOVE = float(os.getenv("ALERT_PRICE_ABOVE", "0"))  # 0 = disabled
ALERT_PRICE_BELOW = float(os.getenv("ALERT_PRICE_BELOW", "0"))  # 0 = disabled

# Update interval (minutes) - set to 60 (1 hour) for Twelve Data API free tier (800/day)
UPDATE_INTERVAL_MINUTES = int(os.getenv("UPDATE_INTERVAL_MINUTES", "60"))

# Egyptian market markup (percentage over international price)
# Egyptian prices include workmanship fees, merchant margins, and taxes
# Calibrated to match real Egyptian market: ~7% markup
EGYPT_MARKUP_PERCENTAGE = float(os.getenv("EGYPT_MARKUP_PERCENTAGE", "7"))  # 7% default

# Logging
LOG_FILE = "gold_tracker.log"
