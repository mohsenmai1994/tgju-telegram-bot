from __future__ import annotations

import os
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Final, Optional

import pytz

# Import custom modules for target site parsing and WebDriver configuration
from TelegramWebScraper import TGJUScraper, __webdriver__


# Configure root logging configuration to record execution diagnostics
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# Establish deterministic file system paths relative to this script's location
BASE_DIR: Final[Path] = Path(__file__).parent
FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"

# Retrieve environment variables for secure Telegram API credentials
BOT_TOKEN: Final[Optional[str]] = os.getenv("BOT_TOKEN")
CHAT_ID: Final[Optional[str]] = os.getenv("CHAT_ID_CURRENCYTEL")


def transmit_to_telegram(message_payload: str) -> None:
    """
    Transmits the generated report to a designated Telegram channel or chat.

    This function issues a synchronous HTTP POST request to the Telegram Bot API.
    It formats the payload as HTML and disables automatic link previews to clean up
    the layout of the message.

    Args:
        message_payload (str): The structured text report to be transmitted.

    Raises:
        RuntimeError: If necessary credentials (BOT_TOKEN, CHAT_ID) are missing from the env.
        requests.Timeout: If the connection to the API endpoint exceeds the threshold.
        requests.RequestException: For underlying network, transport, or HTTP response errors.
    """
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("Missing BOT_TOKEN or CHAT_ID environment variables.")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message_payload,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, data=payload, timeout=15)
        response.raise_for_status()
        logging.info("Telegram message sent successfully.")
    except requests.Timeout:
        logging.error("Telegram request timed out.")
        raise
    except requests.RequestException as exc:
        logging.exception("Failed to send Telegram message: %s", exc)
        raise


def execution_cycle() -> None:
    """
    Orchestrates the scraping pipeline execution sequence.

    This routine performs the following sequential actions:
    1. Initializes the isolated Selenium WebDriver instance.
    2. Runs the web scraping routine on the target domain.
    3. Persists the parsed data to a local text file on the disk (I/O).
    4. dispatches the payload to the remote Telegram server.
    5. Guarantees the destruction of the WebDriver process to prevent memory leaks.
    """
    tehran_tz = pytz.timezone("Asia/Tehran")
    now_tehran = datetime.now(tehran_tz)

    """
    # Restrict execution to regional business hours (09:00 - 20:59 Tehran time)
    if not (11 <= now_tehran.hour < 23):
        logging.info("Outside Tehran working hours. Skipping execution cycle.")
        return
    """
    logging.info("Pipeline started.")

    browser = None
    try:
        # Initialize driver and execute DOM traversal
        browser = __webdriver__()
        scraper = TGJUScraper(browser)
        content = scraper.run()
        
        if content:
            # 1. Write the payload to disk as a persistent text file
            FILE_PATH.write_text(content, encoding="utf-8")
            logging.info(f"Report saved locally to {FILE_PATH.resolve()}")
            
            # 2. Dispatch the text payload to Telegram
            transmit_to_telegram(content)
        else:
            logging.warning("No content generated; file write and Telegram transmission skipped.")       
    finally:
        # Guarantee driver termination inside finally block to prevent orphaned processes
        if browser is not None:
            try:
                browser.quit()
            except Exception:
                logging.exception("Failed to quit browser cleanly.")


if __name__ == "__main__":
    execution_cycle()
