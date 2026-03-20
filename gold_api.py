"""Gold price fetching from FCS API."""

import logging
from datetime import datetime

import requests

import config

logger = logging.getLogger(__name__)

FCS_API_URL = "https://fcsapi.com/api-v3/forex/latest"


def fetch_gold_price() -> dict | None:
    """Fetch current gold price from FCS API (free tier: 100 requests/day).

    Get your free API key at: https://fcsapi.com/pricing-free

    Returns dict with keys:
        - price: current price per ounce (float)
        - price_gram_22k: price per gram 22k (float)
        - bid: bid price (float)
        - ask: ask price (float)
        - timestamp: ISO timestamp (str)
    Returns None if fetch fails.
    """
    try:
        params = {
            "symbol": "XAU/USD",
            "access_key": config.FCS_API_KEY,
            "api_key": config.FCS_API_PUBLIC_KEY,  # Some FCS API endpoints require this
        }

        resp = requests.get(
            FCS_API_URL,
            params=params,
            timeout=15,
        )

        if resp.status_code == 200:
            data = resp.json()

            if data.get("status"):
                price_info = data["response"][0]
                price = float(price_info.get("c", 0))  # Current/close price
                bid = float(price_info.get("b", price))  # Bid
                ask = float(price_info.get("a", price))  # Ask

                # Calculate 22K per gram (1 oz = 31.1035 grams, 22K = 91.67% pure)
                price_gram_22k = (price / 31.1035) * 0.9167

                # Get timestamp from API or use current time
                timestamp_str = price_info.get("tm", "")
                if not timestamp_str:
                    timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                return {
                    "price": price,
                    "price_gram_22k": price_gram_22k,
                    "bid": bid,
                    "ask": ask,
                    "timestamp": timestamp_str,
                }
            else:
                logger.error("FCS API: %s", data.get("message", "Unknown error"))
                return None
        elif resp.status_code == 401:
            logger.error("FCS API: Invalid API key")
        elif resp.status_code == 429:
            logger.error("FCS API: Rate limit exceeded")
        else:
            logger.error("FCS API error %d: %s", resp.status_code, resp.text)
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
