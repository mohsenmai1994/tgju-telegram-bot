import os
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Final, Optional

import pytz

from TelegramWebScraper import TGJUScraper, __webdriver__


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

BASE_DIR: Final[Path] = Path(__file__).parent
FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"

BOT_TOKEN: Final[Optional[str]] = os.getenv("BOT_TOKEN")
CHAT_ID: Final[Optional[str]] = os.getenv("CHAT_ID")


def transmit_to_telegram(message_payload: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("BOT_TOKEN یا CHAT_ID در محیط تنظیم نشده است.")

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
    tehran_tz = pytz.timezone("Asia/Tehran")
    now_tehran = datetime.now(tehran_tz)

    if not (9 <= now_tehran.hour < 21):
        logging.info("Outside Tehran working hours (09:00-20:59). Skipping run.")
        return

    logging.info("Pipeline started.")

    browser = None
    try:
        browser = __webdriver__()
        scraper = TGJUScraper(browser)
        content = scraper.run()
        
        transmit_to_telegram(content)
            
    finally:
        if browser is not None:
            try:
                browser.quit()
            except Exception:
                logging.exception("Failed to quit browser cleanly.")


if __name__ == "__main__":
    execution_cycle()
