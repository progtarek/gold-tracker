"""Telegram notification sender for gold price alerts."""

import logging

import requests

import config

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4096


def _telegram_api() -> str:
    return f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}"


def _send_single_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a single message (must be <= MAX_MESSAGE_LENGTH)."""
    try:
        resp = requests.post(
            f"{_telegram_api()}/sendMessage",
            json={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        if resp.ok:
            logger.info("Telegram notification sent successfully")
            return True
        else:
            logger.error("Telegram API error %d: %s", resp.status_code, resp.text)
            return False
    except requests.RequestException:
        logger.exception("Failed to send Telegram notification")
        return False


def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a message to the configured Telegram chat."""
    if config.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.warning("Telegram bot token not configured - skipping notification")
        return False

    if len(text) <= MAX_MESSAGE_LENGTH:
        return _send_single_message(text, parse_mode)

    # Split if too long (unlikely for gold updates but safe to have)
    chunks = []
    current = ""
    for part in text.split("\n\n"):
        candidate = f"{current}\n\n{part}" if current else part
        if len(candidate) > MAX_MESSAGE_LENGTH:
            if current:
                chunks.append(current)
            current = part
        else:
            current = candidate
    if current:
        chunks.append(current)

    logger.info("Message too long (%d chars), splitting into %d chunks", len(text), len(chunks))
    success = True
    for chunk in chunks:
        if not _send_single_message(chunk, parse_mode):
            success = False
    return success
