"""Gold price fetching from FCS API."""

import logging
from datetime import datetime

import requests

import config

logger = logging.getLogger(__name__)

FCS_API_URL = "https://fcsapi.com/api-v3/forex/latest"


def _fetch_exchange_rate(from_currency: str, to_currency: str) -> float | None:
    """Fetch exchange rate from FCS API."""
    try:
        params = {
            "symbol": f"{from_currency}/{to_currency}",
            "access_key": config.FCS_API_KEY,
        }

        resp = requests.get(
            FCS_API_URL,
            params=params,
            timeout=15,
        )

        if resp.status_code == 200:
            data = resp.json()
            if data.get("status"):
                rate_info = data["response"][0]
                return float(rate_info.get("c", 0))
        return None
    except requests.RequestException as e:
        logger.exception("Failed to fetch exchange rate %s/%s: %s", from_currency, to_currency, e)
        return None


def fetch_gold_price() -> dict | None:
    """Fetch current gold price from FCS API (free tier: 100 requests/day).

    Get your free API key at: https://fcsapi.com/pricing-free

    Returns dict with keys:
        - price: current price per ounce in USD (float)
        - price_gram_24k: price per gram 24k in USD (float)
        - bid: bid price (float)
        - ask: ask price (float)
        - timestamp: ISO timestamp (str)
        - price_egp_24k: price per gram 24k in EGP (float)
        - price_egp_21k: price per gram 21k in EGP (float)
        - price_egp_18k: price per gram 18k in EGP (float)
        - usd_to_egp: USD to EGP exchange rate (float)
    Returns None if fetch fails.
    """
    try:
        params = {
            "symbol": "XAU/USD",
            "access_key": config.FCS_API_KEY,
        }

        resp = requests.get(
            FCS_API_URL,
            params=params,
            timeout=15,
        )

        if resp.status_code == 200:
            data = resp.json()

            # Log full response for debugging
            logger.debug("FCS API Response: %s", data)

            if data.get("status"):
                price_info = data["response"][0]
                price = float(price_info.get("c", 0))  # Current/close price
                bid = float(price_info.get("b", price))  # Bid
                ask = float(price_info.get("a", price))  # Ask

                # Calculate 24K per gram (1 oz = 31.1035 grams, 24K = 99.9% pure)
                price_gram_24k_usd = (price / 31.1035) * 0.999

                # Fetch USD to EGP exchange rate
                usd_to_egp = _fetch_exchange_rate("USD", "EGP")
                price_egp_24k = None
                price_egp_21k = None
                price_egp_18k = None

                if usd_to_egp:
                    # Calculate EGP prices per gram for different karats
                    # 24K = 99.9% pure, 21K = 87.5% pure, 18K = 75% pure
                    # Apply Egyptian market markup (workmanship, margins, taxes)
                    markup_multiplier = 1 + (config.EGYPT_MARKUP_PERCENTAGE / 100)
                    price_egp_24k = price_gram_24k_usd * usd_to_egp * markup_multiplier
                    price_egp_21k = (price / 31.1035) * 0.875 * usd_to_egp * markup_multiplier
                    price_egp_18k = (price / 31.1035) * 0.75 * usd_to_egp * markup_multiplier
                    logger.info("USD to EGP rate: %.2f (Egyptian markup: %d%%)", usd_to_egp, config.EGYPT_MARKUP_PERCENTAGE)
                else:
                    logger.warning("Failed to fetch USD/EGP rate - EGP prices will not be shown")

                # Get timestamp from API or use current time
                timestamp_str = price_info.get("tm", "")
                if not timestamp_str:
                    timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                return {
                    "price": price,
                    "price_gram_24k_usd": price_gram_24k_usd,
                    "bid": bid,
                    "ask": ask,
                    "timestamp": timestamp_str,
                    "price_egp_24k": price_egp_24k,
                    "price_egp_21k": price_egp_21k,
                    "price_egp_18k": price_egp_18k,
                    "usd_to_egp": usd_to_egp,
                }
            else:
                # Enhanced error logging
                error_msg = data.get("msg", data.get("message", "Unknown error"))
                error_code = data.get("code", "N/A")
                logger.error("FCS API Error [code: %s]: %s", error_code, error_msg)
                logger.error("Full API response: %s", data)

                # Check for specific error conditions
                if error_code == 101 or "valid" in str(error_msg).lower() or "unauthorized" in str(error_msg).lower():
                    logger.error("=" * 60)
                    logger.error("API KEY ISSUE DETECTED!")
                    logger.error("Please ensure you've set up FCS API credentials:")
                    logger.error("1. Get free API key: https://fcsapi.com/pricing-free")
                    logger.error("2. Add FCS_API_KEY to GitHub Secrets")
                    logger.error("3. See SETUP.md for detailed instructions")
                    logger.error("=" * 60)
                elif "limit" in str(error_msg).lower() or "quota" in str(error_msg).lower():
                    logger.error("API rate limit or quota exceeded (100 requests/day free tier).")
                return None
        elif resp.status_code == 401:
            logger.error("FCS API: Invalid API key (HTTP 401)")
        elif resp.status_code == 429:
            logger.error("FCS API: Rate limit exceeded (HTTP 429)")
        else:
            logger.error("FCS API HTTP error %d: %s", resp.status_code, resp.text)
        return None
    except requests.RequestException as e:
        logger.exception("Failed to fetch gold price: %s", e)
        return None


def format_price_message(price_data: dict, previous_price: float | None = None) -> str:
    """Format a gold price update message."""
    price = price_data["price"]
    price_gram_24k_usd = price_data.get("price_gram_24k_usd")
    bid = price_data["bid"]
    ask = price_data["ask"]
    timestamp = price_data["timestamp"]
    price_egp_24k = price_data.get("price_egp_24k")
    price_egp_21k = price_data.get("price_egp_21k")
    price_egp_18k = price_data.get("price_egp_18k")
    usd_to_egp = price_data.get("usd_to_egp")

    msg = (
        f"\U0001f4b0 <b>Gold Price Update</b>\n\n"
        f"\U0001f517 <b>${price:.2f}</b> / oz\n"
        f"\U0001f4c8 Bid: ${bid:.2f} | Ask: ${ask:.2f}"
    )

    # Add Egyptian gold prices if available
    if price_egp_24k and price_egp_21k and price_egp_18k:
        msg += (
            f"\n\n\U0001f4b5 <b>Egyptian Gold Prices (per gram)</b>\n"
            f"\U0001f311 24K: <b>EGP {price_egp_24k:,.2f}</b>\n"
            f"\U0001f33a 21K: <b>EGP {price_egp_21k:,.2f}</b>\n"
            f"\U0001f341 18K: <b>EGP {price_egp_18k:,.2f}</b>"
        )
        if usd_to_egp:
            msg += f"\n\U0001f4b2 USD/EGP: {usd_to_egp:.2f} (includes {config.EGYPT_MARKUP_PERCENTAGE}% market markup)"

    msg += f"\n\u23f0 {timestamp}"

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
