"""Main scheduler for gold price tracking."""

import logging
import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler

import config
import gold_api
import notifier

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE),
    ],
)
logger = logging.getLogger("gold-tracker")

# Quiet down APScheduler and urllib3
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# State to track previous price
previous_price: float | None = None
# Track if we've already alerted for thresholds
alerted_above = False
alerted_below = False


def check_and_notify():
    """Fetch gold price, check thresholds, and send notifications."""
    global previous_price, alerted_above, alerted_below

    logger.info("=" * 50)
    logger.info("Checking gold price...")

    price_data = gold_api.fetch_gold_price()
    if not price_data:
        logger.error("Failed to fetch gold price - skipping this cycle")
        return

    current_price = price_data["price"]
    logger.info("Current gold price: $%.2f/oz (previous: $%.2f)", current_price, previous_price or 0)

    # Check threshold alerts
    alerts_sent = []

    # Alert if price goes ABOVE threshold
    if config.ALERT_PRICE_ABOVE > 0:
        if current_price > config.ALERT_PRICE_ABOVE:
            if not alerted_above:
                msg = gold_api.format_alert_message(price_data, "above", config.ALERT_PRICE_ABOVE)
                if notifier.send_message(msg):
                    alerted_above = True
                    alerts_sent.append(f"ABOVE ${config.ALERT_PRICE_ABOVE:.2f}")
                logger.info("Sent ABOVE alert - price is $%.2f", current_price)
        else:
            # Reset alert when price drops back below threshold
            if alerted_above:
                logger.info("Price dropped back below threshold - resetting ABOVE alert")
                alerted_above = False

    # Alert if price goes BELOW threshold
    if config.ALERT_PRICE_BELOW > 0:
        if current_price < config.ALERT_PRICE_BELOW:
            if not alerted_below:
                msg = gold_api.format_alert_message(price_data, "below", config.ALERT_PRICE_BELOW)
                if notifier.send_message(msg):
                    alerted_below = True
                    alerts_sent.append(f"BELOW ${config.ALERT_PRICE_BELOW:.2f}")
                logger.info("Sent BELOW alert - price is $%.2f", current_price)
        else:
            # Reset alert when price rises back above threshold
            if alerted_below:
                logger.info("Price rose back above threshold - resetting BELOW alert")
                alerted_below = False

    # Always send regular price update
    msg = gold_api.format_price_message(price_data, previous_price)
    notifier.send_message(msg)

    previous_price = current_price

    if alerts_sent:
        logger.info("Alerts sent: %s", ", ".join(alerts_sent))

    logger.info("Cycle complete")


def main():
    """Initialize and start the scheduler."""
    logger.info("Gold Price Tracker starting up")

    # Validate config
    if config.GOLDAPI_KEY == "YOUR_GOLDAPI_KEY_HERE":
        logger.error(
            "GoldAPI key not configured! Get a free key at https://www.goldapi.io\n"
            "Set GOLDAPI_KEY in .env file"
        )
        sys.exit(1)

    if config.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "Telegram bot token not configured!\n"
            "Set TELEGRAM_BOT_TOKEN in .env file"
        )
        sys.exit(1)

    logger.info("Configuration:")
    logger.info("  Update interval: %d minutes", config.UPDATE_INTERVAL_MINUTES)
    logger.info("  Alert above: $%s", config.ALERT_PRICE_ABOVE if config.ALERT_PRICE_ABOVE > 0 else "disabled")
    logger.info("  Alert below: $%s", config.ALERT_PRICE_BELOW if config.ALERT_PRICE_BELOW > 0 else "disabled")

    # Run initial check immediately
    logger.info("Running initial price check...")
    check_and_notify()

    # Set up scheduler
    sched = BlockingScheduler()
    sched.add_job(
        check_and_notify,
        "interval",
        minutes=config.UPDATE_INTERVAL_MINUTES,
        id="gold_check",
        max_instances=1,
        coalesce=True,
    )

    # Graceful shutdown
    def shutdown(signum, frame):
        logger.info("Shutting down...")
        sched.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.info(
        "Scheduler started - checking every %d minutes. Press Ctrl+C to stop.",
        config.UPDATE_INTERVAL_MINUTES,
    )
    sched.start()


if __name__ == "__main__":
    main()
