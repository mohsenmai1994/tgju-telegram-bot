from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Final
from urllib.parse import urlparse

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from Scraper import __webdriver__


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("AlanChandScraper")

BASE_URL: Final[str] = "https://alanchand.com"
FILE_PATH: Final[Path] = Path(__file__).resolve().parent / "market_log.txt"
CHANNEL_HANDLE: Final[str] = "@CurrencyTel"
WAIT_SECONDS: Final[int] = 12
NAVIGATION_ATTEMPTS: Final[int] = 3
NUMBER_RE = re.compile(r"(?<!\d)(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?!\d)")
DIGIT_TABLE = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٬٫",
    "01234567890123456789,."
)


def parse_number(raw: str) -> Decimal | None:
    text = (raw or "").translate(DIGIT_TABLE)
    match = NUMBER_RE.search(text)
    if not match:
        return None
    try:
        number = Decimal(match.group(0).replace(",", ""))
        return number if number > 0 else None
    except InvalidOperation:
        return None


def format_number(number: Decimal) -> str:
    return format(number, ",f").rstrip("0").rstrip(".") if number % 1 else format(number, ",.0f")


@dataclass(frozen=True)
class Quote:
    label: str
    path: str
    section: str
    is_irr: bool = True
    unit: str = "تومان"


CURRENCIES: Final[tuple[Quote, ...]] = (
    Quote("☸️ دلار آمریکا", "/en/currencies-price/usd", "/en/currencies-price"),
    Quote("☸️ یورو", "/en/currencies-price/eur", "/en/currencies-price"),
    Quote("☸️ پوند انگلیس", "/en/currencies-price/gbp", "/en/currencies-price"),
    Quote("☸️ لیر ترکیه", "/en/currencies-price/try", "/en/currencies-price"),
    Quote("☸️ فرانک سوئیس", "/en/currencies-price/chf", "/en/currencies-price"),
    Quote("☸️ یوان چین", "/en/currencies-price/cny", "/en/currencies-price"),
)

COINS_AND_GOLD: Final[tuple[Quote, ...]] = (
    Quote("✴️ سکه بهار آزادی", "/en/gold-price/bahar", "/en/gold-price"),
    Quote("✴️ نیم سکه", "/en/gold-price/nim", "/en/gold-price"),
    Quote("✴️ ربع سکه", "/en/gold-price/rob", "/en/gold-price"),
    Quote("✴️ انس طلا", "/en/gold-price/usd_xau", "/en/gold-price", False, "دلار"),
    Quote("✴️ طلای ۱۸ عیار", "/en/gold-price/18ayar", "/en/gold-price"),
)

ENERGY: Final[tuple[Quote, ...]] = (
    Quote("✴️ نفت برنت", "/en/energy/brent-oil", "/en/energy", False, "دلار/بشکه"),
)

CRYPTO: Final[tuple[Quote, ...]] = (
    Quote("✴️ بیت کوین", "/en/crypto-price/btc", "/en/crypto-price", False, "دلار"),
    Quote("✴️ تتر", "/en/crypto-price/usdt", "/en/crypto-price"),
)

ALL_QUOTES: Final[tuple[Quote, ...]] = (*CURRENCIES, *COINS_AND_GOLD, *ENERGY, *CRYPTO)


class AlanChandScraper:
    """Read prices from the English homepage, then fallback to category pages."""

    TARGET_URL: Final[str] = BASE_URL + "/en"
    BASE_DIR: Final[Path] = Path(__file__).resolve().parent
    FILE_PATH: Final[Path] = FILE_PATH
    CHANNEL_HANDLE: Final[str] = CHANNEL_HANDLE

    def __init__(self, driver) -> None:
        self.driver = driver
        self.wait = WebDriverWait(driver, WAIT_SECONDS)

    def visit(self, page: str) -> bool:
        """Attempt navigation repeatedly; return False if no usable <main> appears."""
        target = BASE_URL + page
        for attempt in range(1, NAVIGATION_ATTEMPTS + 1):
            try:
                self.driver.get(target)
                self.wait.until(lambda d: bool(d.find_elements(By.TAG_NAME, "main")))
                logger.info("Loaded %s", page)
                return True
            except (TimeoutException, WebDriverException) as exc:
                logger.warning(
                    "Cannot load %s (attempt %s/%s): %s; current_url=%r title=%r",
                    page, attempt, NAVIGATION_ATTEMPTS, type(exc).__name__,
                    getattr(self.driver, "current_url", None),
                    getattr(self.driver, "title", None),
                )
        return False

    def collect_visible_quotes(self, page: str, needed: tuple[Quote, ...]) -> dict[str, Decimal]:
        """Read only the price cell in the table row for each matching asset URL.

        On /en the BTC price is in USD (column 2). On /en/crypto-price,
        the BTC USD price is in column 4. Other assets use column 2.
        """
        wanted = {q.path: q for q in needed}
        values: dict[str, Decimal] = {}
        for link in self.driver.find_elements(By.XPATH, "//main//a[@href]"):
            href = urlparse(link.get_attribute("href") or "").path.rstrip("/")
            quote = wanted.get(href)
            if quote is None or href in values:
                continue

            for row in link.find_elements(By.XPATH, "ancestor::tr[1]"):
                cells = row.find_elements(By.XPATH, "./td")
                column = 3 if page == "/en/crypto-price" and quote.path.endswith("/btc") else 1
                if len(cells) <= column:
                    continue
                number = parse_number(cells[column].text)
                if number is None:
                    continue
                values[href] = number / Decimal(10) if quote.is_irr else number
                break
        return values

    def build_report(self) -> str:
        found: dict[str, Decimal] = {}

        # All 14 assets also appear in tables on the homepage. This typically
        # avoids the failing navigation to /en/energy entirely.
        if self.visit("/en"):
            found.update(self.collect_visible_quotes("/en", ALL_QUOTES))
            logger.info("Homepage: %s/%s prices retrieved", len(found), len(ALL_QUOTES))

        # Only load a specialist page when its price was missing on the homepage.
        for page in ("/en/currencies-price", "/en/gold-price", "/en/energy", "/en/crypto-price"):
            needed = tuple(q for q in ALL_QUOTES if q.section == page and q.path not in found)
            if not needed:
                continue
            logger.info("Fallback %s for %s missing prices", page, len(needed))
            if not self.visit(page):
                continue
            found.update(self.collect_visible_quotes(page, needed))

        missing = [q.label for q in ALL_QUOTES if q.path not in found]
        if missing:
            raise RuntimeError(
                "Incomplete price report; refusing to overwrite market_log.txt. "
                "Missing: " + ", ".join(missing)
            )

        lines = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین", ""]
        for q in ALL_QUOTES:
            rendered = f"{format_number(found[q.path])} {q.unit}"
            logger.info("%s: %s", q.label, rendered)
            lines.append(f"{q.label}: {rendered}")
        lines.extend(["", f"🆔 {self.CHANNEL_HANDLE}"])
        return "\n".join(lines)

    def run(self) -> str:
        report = self.build_report()
        # Preserve the last good file if any required price could not be read.
        self.FILE_PATH.write_text(report, encoding="utf-8")
        logger.info("Report saved to %s", self.FILE_PATH)
        return report


class TGJUScraper(AlanChandScraper):
    """Backward-compatible class name imported by existing main.py."""


def main() -> None:
    driver = __webdriver__()
    try:
        print(TGJUScraper(driver).run())
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
