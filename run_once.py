"""Run a single gold price check and notify - designed for GitHub Actions."""

import logging
import os
import sys

import config
import gold_api
import notifier

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# Ensure required env vars are set
if not os.getenv("GOLDAPI_KEY"):
    config.GOLDAPI_KEY = os.environ["GOLDAPI_KEY"]
if not os.getenv("TELEGRAM_BOT_TOKEN"):
    config.TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
if not os.getenv("TELEGRAM_CHAT_ID"):
    config.TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Optional: override thresholds from env/secrets
if "ALERT_PRICE_ABOVE" in os.environ:
    config.ALERT_PRICE_ABOVE = float(os.environ["ALERT_PRICE_ABOVE"])
if "ALERT_PRICE_BELOW" in os.environ:
    config.ALERT_PRICE_BELOW = float(os.environ["ALERT_PRICE_BELOW"])


def main():
    """Run one price check cycle."""
    logger = logging.getLogger("gold-tracker")
    logger.info("Gold Price Tracker - single run")

    # Log config
    logger.info("Configuration:")
    logger.info("  Alert above: $%s", config.ALERT_PRICE_ABOVE if config.ALERT_PRICE_ABOVE > 0 else "disabled")
    logger.info("  Alert below: $%s", config.ALERT_PRICE_BELOW if config.ALERT_PRICE_BELOW > 0 else "disabled")

    # Fetch price
    logger.info("Fetching gold price...")
    price_data = gold_api.fetch_gold_price()
    if not price_data:
        logger.error("Failed to fetch gold price")
        sys.exit(1)

    current_price = price_data["price"]
    logger.info("Current gold price: $%.2f/oz", current_price)

    # Note: In GitHub Actions, we don't track previous_price between runs
    # So we'll just show the current price

    # Check threshold alerts
    alerted = False

    if config.ALERT_PRICE_ABOVE > 0 and current_price > config.ALERT_PRICE_ABOVE:
        msg = gold_api.format_alert_message(price_data, "above", config.ALERT_PRICE_ABOVE)
        notifier.send_message(msg)
        logger.info("Sent ABOVE alert")
        alerted = True

    if config.ALERT_PRICE_BELOW > 0 and current_price < config.ALERT_PRICE_BELOW:
        msg = gold_api.format_alert_message(price_data, "below", config.ALERT_PRICE_BELOW)
        notifier.send_message(msg)
        logger.info("Sent BELOW alert")
        alerted = True

    # Always send price update
    msg = gold_api.format_price_message(price_data, previous_price=None)
    notifier.send_message(msg)

    if alerted:
        logger.info("Price alert sent!")
    else:
        logger.info("Price update sent")

    logger.info("Run complete")


if __name__ == "__main__":
    main()
