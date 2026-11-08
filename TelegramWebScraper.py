from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from decimal import Decimal
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
WAIT_SECONDS: Final[int] = 15

# The English site displays Iranian market prices in IRR.
# Convert those figures to toman only when is_irr=True.
NUMBER_RE = re.compile(r"(?<!\d)(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?!\d)")
USD_RE = re.compile(r"\$\s*((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)")


def normalize_digits(value: str) -> str:
    return value.translate(str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٬٫",
        "01234567890123456789,."
    ))


def parse_number(value: str, *, require_dollar_sign: bool = False) -> Decimal | None:
    value = normalize_digits(value or "")
    match = (USD_RE if require_dollar_sign else NUMBER_RE).search(value)
    if not match:
        return None
    number = match.group(1) if require_dollar_sign else match.group(0)
    try:
        result = Decimal(number.replace(",", ""))
        return result if result > 0 else None
    except ArithmeticError:
        return None


def format_number(value: Decimal) -> str:
    return f"{value:,.8f}".rstrip("0").rstrip(".") if value % 1 else f"{value:,.0f}"


@dataclass(frozen=True)
class Quote:
    label: str
    path: str
    name: str
    column: int                # Zero-based column of the source table
    is_irr: bool = True        # Convert IRR to toman
    usd_card: bool = False     # BTC fallback: extract its USD price, not its IRR price
    unit: str = "تومان"


CURRENCIES: Final[tuple[Quote, ...]] = (
    Quote("☸️ دلار آمریکا", "/en/currencies-price/usd", "US Dollar", 1),
    Quote("☸️ یورو", "/en/currencies-price/eur", "Euro", 1),
    Quote("☸️ پوند انگلیس", "/en/currencies-price/gbp", "British Pound", 1),
    Quote("☸️ لیر ترکیه", "/en/currencies-price/try", "Turkish Lira", 1),
    Quote("☸️ فرانک سوئیس", "/en/currencies-price/chf", "Swiss Franc", 1),
    Quote("☸️ یوان چین", "/en/currencies-price/cny", "Chinese Yuan", 1),
)

COINS_AND_GOLD: Final[tuple[Quote, ...]] = (
    Quote("✴️ سکه بهار آزادی", "/en/gold-price/bahar", "Bahar Azadi Coin", 1),
    Quote("✴️ نیم سکه", "/en/gold-price/nim", "Half Coin", 1),
    Quote("✴️ ربع سکه", "/en/gold-price/rob", "Quarter Coin", 1),
    Quote("✴️ انس طلا", "/en/gold-price/usd_xau", "Gold Ounce", 1,
          is_irr=False, unit="دلار"),
    Quote("✴️ طلای ۱۸ عیار", "/en/gold-price/18ayar", "18K Gold per Gram", 1),
)

ENERGY: Final[tuple[Quote, ...]] = (
    Quote("✴️ نفت برنت", "/en/energy/brent-oil", "Brent Crude Oil", 1,
          is_irr=False, unit="دلار/بشکه"),
)

CRYPTO: Final[tuple[Quote, ...]] = (
    Quote("✴️ بیت کوین", "/en/crypto-price/btc", "Bitcoin", 3,
          is_irr=False, usd_card=True, unit="دلار"),
    Quote("✴️ تتر", "/en/crypto-price/usdt", "Tether", 1),
)


class AlanChandScraper:
    def __init__(self, driver) -> None:
        self.driver = driver
        self.wait = WebDriverWait(driver, WAIT_SECONDS)

    def visit(self, page: str) -> None:
        self.driver.get(BASE_URL + page)
        self.wait.until(lambda d: d.find_elements(By.TAG_NAME, "main"))
        logger.info("Loaded %s", page)

    @staticmethod
    def _after_label(raw: str, label: str) -> str:
        """Avoid parsing the 18 in '18K Gold' as the actual gold price."""
        pos = raw.lower().find(label.lower())
        return raw[pos + len(label):] if pos >= 0 else ""

    def _extract_quote(self, quote: Quote) -> Decimal | None:
        # Match the entire destination path: /usd must not match /usd-hav.
        for link in self.driver.find_elements(By.XPATH, "//main//a[@href]"):
            href = urlparse(link.get_attribute("href") or "").path.rstrip("/")
            if href != quote.path:
                continue

            # Table-based layout: the value is in a known price column.
            rows = link.find_elements(By.XPATH, "ancestor::tr[1]")
            if rows:
                cells = rows[0].find_elements(By.XPATH, "./td")
                if len(cells) > quote.column:
                    number = parse_number(cells[quote.column].text)
                    if number is not None:
                        return number

            # Card-based layout: the price may be within the clickable card
            # or its immediate parent. Always extract text after the item name.
            candidates = [link]
            candidates += link.find_elements(By.XPATH, "./..")
            candidates += link.find_elements(By.XPATH, "./../..")
            for candidate in candidates:
                raw = normalize_digits(candidate.text)
                tail = self._after_label(raw, quote.name)
                if not tail:
                    continue
                number = parse_number(tail, require_dollar_sign=quote.usd_card)
                if number is not None:
                    return number

        return None

    def read_quote(self, quote: Quote) -> Decimal:
        try:
            result = self.wait.until(lambda _driver: self._extract_quote(quote))
        except TimeoutException as exc:
            raise RuntimeError(
                f"Could not find a reliable price for {quote.label} "
                f"({quote.path}) on {self.driver.current_url}"
            ) from exc
        return result / Decimal(10) if quote.is_irr else result

    def build_report(self) -> str:
        values: dict[str, str] = {}
        groups = (
            ("/en/currencies-price", CURRENCIES),
            ("/en/gold-price", COINS_AND_GOLD),
            ("/en/energy", ENERGY),
            ("/en/crypto-price", CRYPTO),
        )

        for page, quotes in groups:
            self.visit(page)
            for quote in quotes:
                result = self.read_quote(quote)
                values[quote.path] = f"{format_number(result)} {quote.unit}"
                logger.info("%s: %s", quote.label, values[quote.path])

        lines = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین", ""]
        # Preserve the intended order of the original report.
        output_order = (
            *CURRENCIES, *COINS_AND_GOLD[:3],
            COINS_AND_GOLD[3], COINS_AND_GOLD[4],
            ENERGY[0], CRYPTO[0], CRYPTO[1],
        )
        lines.extend(f"{quote.label}: {values[quote.path]}" for quote in output_order)
        lines.extend(["", f"🆔 {CHANNEL_HANDLE}"])
        return "\n".join(lines)

    def run(self) -> str:
        report = self.build_report()
        # Write only after EVERY required price is retrieved successfully.
        FILE_PATH.write_text(report, encoding="utf-8")
        logger.info("Report saved to %s", FILE_PATH)
        return report


class TGJUScraper(AlanChandScraper):
    """Backward-compatible public class used by the existing main.py."""

    TARGET_URL: Final[str] = BASE_URL + "/en/currencies-price"
    BASE_DIR: Final[Path] = Path(__file__).resolve().parent
    FILE_PATH: Final[Path] = FILE_PATH
    CHANNEL_HANDLE: Final[str] = CHANNEL_HANDLE


def main() -> None:
    driver = __webdriver__()
    try:
        print(TGJUScraper(driver).run())
    except (RuntimeError, WebDriverException):
        logger.exception("Scraping failed. The previous report has been preserved.")
        raise
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
