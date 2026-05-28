import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Final, List

import pytz

from Scraper import __webdriver__


@dataclass(frozen=True)
class AssetMetadata:
    """
    Represents a single market asset with its extraction selector
    and display configuration.
    """
    name: str
    xpath: str
    unit: str
    symbol: str


class TGJUScraper:
    """
    Extracts market data from TGJU and writes the formatted result
    to a local text file for downstream Telegram delivery.
    """

    TARGET_URL: Final[str] = "https://www.tgju.org/"
    BASE_DIR: Final[Path] = Path(__file__).parent
    FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"
    CHANNEL_HANDLE: Final[str] = "@aghayebazar_official"

    # Asset catalog ordered exactly as intended for Telegram output.
    ASSETS: Final[List[AssetMetadata]] = [
        # Foreign exchange instruments
        AssetMetadata("دلار آمريکا", '//*[@id="l-price_dollar_rl"]/span[1]', "ریال", "☸️"),
        AssetMetadata("یورو", '//*[@id="l-price_eur"]/span[1]', "ریال", "☸️"),
        AssetMetadata("درهم امارات", '//*[@id="l-price_aed"]/span[1]', "ریال", "☸️"),
        AssetMetadata("پوند انگلیس", '//*[@id="l-price_gbp"]/span[1]', "ریال", "☸️"),
        AssetMetadata("لیر ترکیه", '//*[@id="l-price_try"]/span[1]', "ریال", "☸️"),
        AssetMetadata("فرانک سوئیس", '//*[@id="l-price_chf"]/span[1]', "ریال", "☸️"),
        AssetMetadata("یوان چین", '//*[@id="l-price_cny"]/span[1]', "ریال", "☸️"),
        AssetMetadata("ین ژاپن", '//*[@id="l-price_jpy"]/span[1]', "ریال", "☸️"),
        AssetMetadata("وون کره جنوبی", '//*[@id="l-price_krw"]/span[1]', "ریال", "☸️"),
        AssetMetadata("دلار کانادا", '//*[@id="l-price_cad"]/span[1]', "ریال", "☸️"),
        AssetMetadata("دلار استرالیا", '//*[@id="l-price_aud"]/span[1]', "ریال", "☸️"),
        AssetMetadata("دلار نیوزلند", '//*[@id="l-price_nzd"]/span[1]', "ریال", "☸️"),

        # Gold, coin, and digital assets
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

    def __init__(self) -> None:
        """Initializes the scraper with a browser driver instance."""
        self.logger = logging.getLogger(__name__)
        self.driver = __webdriver__()

    def _extract_price(self, xpath: str) -> str:
        """
        Reads the text content of a target element.
        Returns a placeholder if the element is not available.
        """
        try:
            value = self.driver.read_text(xpath)
            return value.strip() if value else "-"
        except Exception as exc:
            self.logger.warning("Failed to extract XPath %s: %s", xpath, exc)
            return "-"

    def _extract_persian_timestamp(self) -> str:
        """
        Builds a Tehran-local timestamp string.
        Note: this is a Persian-language formatted timestamp, not a Jalali conversion.
        """
        tehran_tz = pytz.timezone("Asia/Tehran")
        now = datetime.now(tehran_tz)

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

        weekday_name = weekdays[now.weekday()]
        month_name = months[now.month]
        return f"{weekday_name} {now.day} {month_name} - {now.strftime('%H:%M:%S')}"

    def _build_report(self) -> str:
        """
        Creates the final Telegram-ready message using the requested layout.
        """
        lines: List[str] = [
            "#نرخ_ارز #سکه #طلا #دلار #بیتکوین",
            ""
        ]

        for asset in self.ASSETS:
            value = self._extract_price(asset.xpath)
            lines.append(f"{asset.symbol} {asset.name}: {value} {asset.unit}")

        lines.extend([
            "",
            self._extract_persian_timestamp(),
            f"ID: {self.CHANNEL_HANDLE}",
        ])

        return "\n".join(lines)

    def run(self) -> str:
        """
        Opens the target website, extracts all required data,
        stores the result in market_log.txt, and returns the message.
        """
        try:
            self.logger.info("Opening target URL: %s", self.TARGET_URL)
            self.driver.get(self.TARGET_URL)
            self.driver.implicitly_wait(10)

            message = self._build_report()
            self.FILE_PATH.write_text(message, encoding="utf-8")

            self.logger.info("Market report saved to %s", self.FILE_PATH)
            return message

        finally:
            try:
                self.driver.quit()
            except Exception:
                pass
