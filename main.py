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

# دریافت آی‌دی‌ها با امکان Fallback به متغیر قدیمی CHAT_ID در صورت نیاز
CHAT_ID_CURRENCYTEL: Final[Optional[str]] = os.getenv("CHAT_ID_CURRENCYTEL") or os.getenv("CHAT_ID")
CHAT_ID_ZVTNI_TIMES: Final[Optional[str]] = os.getenv("CHAT_ID_ZVTNI_TIMES")


def normalize_chat_id(chat_id: str) -> str:
    """
    نرمال‌سازی چت آی‌دی: اگر با -100 شروع نشود و علامت @ نداشته باشد،
    یک @ به ابتدای آن اضافه می‌کند.
    """
    chat_id = chat_id.strip()
    if not chat_id.startswith("-100") and not chat_id.startswith("@"):
        return f"@{chat_id}"
    return chat_id


def transmit_to_telegram(message_payload: str, chat_id: str) -> None:
    """
    Transmits the generated report to a designated Telegram channel or chat.
    """
    if not BOT_TOKEN:
        raise RuntimeError("Missing BOT_TOKEN environment variable.")

    # نرمال‌سازی آی‌دی برای پیشگیری از خطای تلگرام
    normalized_id = normalize_chat_id(chat_id)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": normalized_id,
        "text": message_payload,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, data=payload, timeout=15)
        response.raise_for_status()
        logging.info(f"Telegram message sent successfully to {normalized_id}")
    except requests.Timeout:
        logging.error(f"Telegram request timed out for {normalized_id}")
        raise
    except requests.RequestException as exc:
        # در صورت خطا، پاسخ سرور تلگرام را لاگ می‌کند تا علت دقیق مشخص شود (مثلاً ادمین نبودن ربات)
        if exc.response is not None:
            logging.error(f"Telegram API error response: {exc.response.text}")
        logging.exception(f"Failed to send Telegram message to {normalized_id}: {exc}")
        raise


def execution_cycle() -> None:
    """
    Orchestrates the scraping pipeline execution sequence.
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
            
            # تهیه لیست کانال‌هایی که باید پیام ارسال شود
            targets = []
            if CHAT_ID_CURRENCYTEL:
                targets.append(CHAT_ID_CURRENCYTEL)
            if CHAT_ID_ZVTNI_TIMES:
                targets.append(CHAT_ID_ZVTNI_TIMES)

            if not targets:
                logging.error("No Telegram Chat IDs configured in environment variables.")
                return

            # 2. Dispatch the text payload to each Telegram channel independently
            for target in targets:
                try:
                    transmit_to_telegram(content, target)
                except Exception as e:
                    logging.error(f"Skipping sending to {target} due to error: {e}")
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
