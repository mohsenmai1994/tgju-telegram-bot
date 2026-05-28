from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, List, Optional

import pytz
from selenium.webdriver.common.by import By

from Scraper import __webdriver__


@dataclass(frozen=True)
class AssetMetadata:
    name: str
    xpath: str
    unit: str
    symbol: str


class TGJUScraper:
    """
    TGJU market data scraper.

    Receives an already-created browser driver and extracts market values
    from TGJU using XPath selectors, then writes the final report to a file.
    """

    TARGET_URL: Final[str] = "https://www.tgju.org/"
    BASE_DIR: Final[Path] = Path(__file__).parent
    FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"
    CHANNEL_HANDLE: Final[str] = "@aghayebazar_official"

    ASSETS: Final[List[AssetMetadata]] = [
        AssetMetadata("دلار آمریکا", '//*[@id="l-price_dollar_rl"]/span[1]', "ریال", "☸️"),
        AssetMetadata("یورو", '//*[@id="l-price_eur"]/span[1]', "ریال", "☸️"),
        AssetMetadata("درهم امارات", '//*[@id="l-price_aed"]/span[1]', "ریال", "☸️"),
        AssetMetadata("پوند انگلیس", '//*[@id="l-price_gbp"]/span[1]', "ریال", "☸️"),
        AssetMetadata("لیر ترکیه", '//*[@id="l-price_try"]/span[1]', "ریال", "☸️"),
        AssetMetadata("فرانک سوئیس", '//*[@id="l-price_chf"]/span[1]', "ریال", "☸️"),
        AssetMetadata("یوان چین", '//*[@id="l-price_cny"]/span[1]', "ریال", "☸️"),
        AssetMetadata("ین ژاپن", '//*[@id="l-price_jpy"]/span[1]', "ریال", "☸️"),
        AssetMetadata("دلار کانادا", '//*[@id="l-price_cad"]/span[1]', "ریال", "☸️"),
        AssetMetadata("دلار استرالیا", '//*[@id="l-price_aud"]/span[1]', "ریال", "☸️"),
        AssetMetadata("دلار نیوزلند", '//*[@id="l-price_nzd"]/span[1]', "ریال", "☸️"),
        AssetMetadata("سکه امامی", '//*[@id="l-coin_sekee"]/span[1]', "ریال", "✴️"),
        AssetMetadata("سکه بهار آزادی", '//*[@id="l-price_bahar"]/span[1]', "ریال", "✴️"),
        AssetMetadata("نیم سکه", '//*[@id="l-coin_nim"]/span[1]', "ریال", "✴️"),
        AssetMetadata("ربع سکه", '//*[@id="l-coin_rob"]/span[1]', "ریال", "✴️"),
        AssetMetadata("سکه گرمی", '//*[@id="l-price_gerami"]/span[1]', "ریال", "✴️"),
        AssetMetadata("انس طلا", '//*[@id="l-ons"]/span[1]', "دلار", "✴️"),
        AssetMetadata("طلای 18 عیار", '//*[@id="l-geram18"]/span[1]', "ریال", "✴️"),
        AssetMetadata("طلای 24 عیار", '//*[@id="l-geram24"]/span[1]', "ریال", "✴️"),
        AssetMetadata("طلای دست دوم", '//*[@id="l-gold_rent_second"]/span[1]', "ریال", "✴️"),
        AssetMetadata("تتر", '//*[@id="l-crypto-tether"]/span[1]', "ریال", "✴️"),
        AssetMetadata("بیت کوین", '//*[@id="l-crypto-bitcoin"]/span[1]', "دلار", "✴️"),
    ]

    def __init__(self, driver) -> None:
        self.driver = driver
        self.logger = logging.getLogger(__name__)
        self._page_text: str = ""

    def _normalize_text(self, text: str) -> str:
        if not text:
            return "-"
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def _extract_text_by_xpath(self, xpath: str) -> str:
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            value = element.text or element.get_attribute("textContent") or "-"
            return self._normalize_text(value)
        except Exception as exc:
            self.logger.warning("XPath extract failed for %s: %s", xpath, exc)
            return "-"

    def _extract_numeric_value(self, text: str) -> str:
        if not text:
            return "-"
        match = re.search(r"[\d,]+(?:\.\d+)?", text)
        return match.group(0) if match else text

    def _extract_tehran_timestamp(self) -> str:
        tz = pytz.timezone("Asia/Tehran")
        now = datetime.now(tz)

        weekdays = {
            0: "دوشنبه",
            1: "سه‌شنبه",
            2: "چهارشنبه",
            3: "پنج‌شنبه",
            4: "جمعه",
            5: "شنبه",
            6: "یکشنبه",
        }

        months = {
            1: "ژانویه",
            2: "فوریه",
            3: "مارس",
            4: "آوریل",
            5: "مه",
            6: "ژوئن",
            7: "ژوئیه",
            8: "اوت",
            9: "سپتامبر",
            10: "اکتبر",
            11: "نوامبر",
            12: "دسامبر",
        }

        return f"{weekdays[now.weekday()]} {now.day} {months[now.month]} - {now.strftime('%H:%M:%S')}"

    def _build_message(self) -> str:
        lines: List[str] = [
            "#نرخ_ارز #سکه #طلا #بیتکوین",
            "",
        ]

        for asset in self.ASSETS:
            raw_value = self._extract_text_by_xpath(asset.xpath)
            value = self._extract_numeric_value(raw_value)
            lines.append(f"{asset.symbol} {asset.name}: {value} {asset.unit}")

        lines.extend([
            "",
            self._extract_tehran_timestamp(),
            f"ID: {self.CHANNEL_HANDLE}",
        ])

        return "\n".join(lines)

    def run(self) -> str:
        try:
            self.logger.info("Opening TGJU: %s", self.TARGET_URL)
            self.driver.get(self.TARGET_URL)

            # Give the page a moment to render dynamic content
            try:
                self.driver.implicitly_wait(5)
            except Exception:
                pass

            message = self._build_message()
            self.FILE_PATH.write_text(message, encoding="utf-8")
            self._page_text = message

            self.logger.info("Saved market log to %s", self.FILE_PATH)
            return message

        finally:
            # Do not quit here if main.py is responsible for lifecycle management.
            # If main.py does not quit, this can be uncommented later.
            pass
