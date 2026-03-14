"""Gold price fetching from GoldAPI.io."""

import logging

import requests

import config

logger = logging.getLogger(__name__)

GOLDAPI_URL = "https://www.goldapi.io/api/XAU/USD"


def fetch_gold_price() -> dict | None:
    """Fetch current gold price from GoldAPI.io.

    Returns dict with keys:
        - price: current price per ounce (float)
        - price_gram_22k: price per gram 22k (float)
        - bid: bid price (float)
        - ask: ask price (float)
        - timestamp: ISO timestamp (str)
    Returns None if fetch fails.
    """
    try:
        resp = requests.get(
            GOLDAPI_URL,
            headers={"x-access-token": config.GOLDAPI_KEY},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "price": float(data.get("price", 0)),
                "price_gram_22k": float(data.get("price_gram_22k", 0)),
                "bid": float(data.get("bid", 0)),
                "ask": float(data.get("ask", 0)),
                "timestamp": data.get("timestamp", ""),
            }
        elif resp.status_code == 401:
            logger.error("GoldAPI: Invalid API key")
        elif resp.status_code == 429:
            logger.error("GoldAPI: Rate limit exceeded")
        else:
            logger.error("GoldAPI error %d: %s", resp.status_code, resp.text)
        return None
    except requests.RequestException as e:
        logger.exception("Failed to fetch gold price: %s", e)
        return None


def format_price_message(price_data: dict, previous_price: float | None = None) -> str:
    """Format a gold price update message."""
    price = price_data["price"]
    price_gram = price_data["price_gram_22k"]
    bid = price_data["bid"]
    ask = price_data["ask"]
    timestamp = price_data["timestamp"]

    msg = (
        f"\U0001f4b0 <b>Gold Price Update</b>\n\n"
        f"\U0001f517 <b>${price:.2f}</b> / oz\n"
        f"\U0001f4aa 22K: <b>${price_gram:.2f}</b> / gram\n"
        f"\U0001f4c8 Bid: ${bid:.2f} | Ask: ${ask:.2f}\n"
        f"\u23f0 {timestamp}"
    )

    if previous_price is not None:
        diff = price - previous_price
        pct = (diff / previous_price) * 100 if previous_price > 0 else 0
        if diff > 0:
            arrow = "\U0001f7e2"
            msg += f"\n{arrow} <b>+${diff:.2f} (+{pct:.2f}%)</b> since last update"
        elif diff < 0:
            arrow = "\U0001f534"
            msg += f"\n{arrow} <b>-${abs(diff):.2f} ({pct:.2f}%)</b> since last update"
        else:
            msg += "\n\u2796 No change since last update"

    return msg


def format_alert_message(price_data: dict, alert_type: str, threshold: float) -> str:
    """Format a price alert message."""
    price = price_data["price"]
    timestamp = price_data["timestamp"]

    if alert_type == "above":
        emoji = "\U0001f534"  # red circle
        title = "Price ABOVE Alert!"
    else:
        emoji = "\U0001f7e2"  # green circle
        title = "Price BELOW Alert!"

    return (
        f"{emoji} <b>{title}</b>\n\n"
        f"\U0001f4b0 Current Price: <b>${price:.2f}</b> / oz\n"
        f"\U0001f4c1 Threshold: ${threshold:.2f}\n"
        f"\u23f0 {timestamp}"
    )
