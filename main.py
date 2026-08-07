from __future__ import annotations

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

# دو کانال
CHAT_IDS = [
    os.getenv("CHAT_ID_CURRENCYTEL"),
    os.getenv("CHAT_ID_ZVTNI_TIMES"),
]


def transmit_to_telegram(message_payload: str, chat_id: str) -> None:
    if not BOT_TOKEN or not chat_id:
        raise RuntimeError("Missing BOT_TOKEN or chat_id environment variables.")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_payload,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = requests.post(url, data=payload, timeout=15)
    response.raise_for_status()
    logging.info("Telegram message sent successfully to %s", chat_id)


def execution_cycle() -> None:
    tehran_tz = pytz.timezone("Asia/Tehran")
    now_tehran = datetime.now(tehran_tz)

    logging.info("Pipeline started.")

    browser = None
    try:
        browser = __webdriver__()
        scraper = TGJUScraper(browser)
        content = scraper.run()

        if content:
            FILE_PATH.write_text(content, encoding="utf-8")
            logging.info(f"Report saved locally to {FILE_PATH.resolve()}")

            for chat_id in CHAT_IDS:
                if chat_id:
                    transmit_to_telegram(content, chat_id)
        else:
            logging.warning("No content generated; skipping.")
    finally:
        if browser is not None:
            try:
                browser.quit()
            except Exception:
                logging.exception("Failed to quit browser cleanly.")


if __name__ == "__main__":
    execution_cycle()
