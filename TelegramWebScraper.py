from __future__ import annotations

import logging
import os
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


logger = logging.getLogger("AlanChandScraper")
BASE_URL: Final = "https://alanchand.com"
OUTPUT_FILE: Final = Path(__file__).resolve().parent / "market_log.txt"
WAIT_SECONDS: Final = 12
# Comma, dot, English, Persian and Arabic-Indic digits are supported.
DIGIT_TRANSLATION: Final = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٬٫", "01234567890123456789,."
)
NUM: Final = r"(?<![\w])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?![\w])"
NUMBER_RE: Final = re.compile(NUM)


def numbers_in(text: str):
    """Yield positive, non-percentage numbers from any small price card."""
    for match in NUMBER_RE.finditer((text or "").translate(DIGIT_TRANSLATION)):
        if (text or "").translate(DIGIT_TRANSLATION)[match.end():].lstrip().startswith(("%", "٪")):
            continue
        try:
            value = Decimal(match.group().replace(",", ""))
        except InvalidOperation:
            continue
        if value > 0:
            yield value


def fmt(number: Decimal) -> str:
    s = format(number, ",f")
    return s.rstrip("0").rstrip(".") if "." in s else s


@dataclass(frozen=True)
class Quote:
    label: str
    path: str
    section: str
    heading: str
    minimum: Decimal
    maximum: Decimal
    unit: str = "تومان"
    in_rials: bool = True


Q: Final[tuple[Quote, ...]] = (
    Quote("☸️ دلار آمریکا", "/en/currencies-price/usd", "/en/currencies-price", "US Dollar", Decimal("10000"), Decimal("1000000000")),
    Quote("☸️ یورو", "/en/currencies-price/eur", "/en/currencies-price", "Euro", Decimal("10000"), Decimal("1000000000")),
    Quote("☸️ پوند انگلیس", "/en/currencies-price/gbp", "/en/currencies-price", "British Pound", Decimal("10000"), Decimal("1000000000")),
    Quote("☸️ لیر ترکیه", "/en/currencies-price/try", "/en/currencies-price", "Turkish Lira", Decimal("1000"), Decimal("100000000")),
    Quote("☸️ فرانک سوئیس", "/en/currencies-price/chf", "/en/currencies-price", "Swiss Franc", Decimal("10000"), Decimal("1000000000")),
    Quote("☸️ یوان چین", "/en/currencies-price/cny", "/en/currencies-price", "Chinese Yuan", Decimal("1000"), Decimal("1000000000")),
    Quote("✴️ سکه بهار آزادی", "/en/gold-price/bahar", "/en/gold-price", "Bahar Azadi Coin", Decimal("1000000"), Decimal("1000000000000")),
    Quote("✴️ نیم سکه", "/en/gold-price/nim", "/en/gold-price", "Half Coin", Decimal("1000000"), Decimal("1000000000000")),
    Quote("✴️ ربع سکه", "/en/gold-price/rob", "/en/gold-price", "Quarter Coin", Decimal("1000000"), Decimal("1000000000000")),
    Quote("✴️ انس طلا", "/en/gold-price/usd_xau", "/en/gold-price", "Gold Ounce to US Dollar", Decimal("100"), Decimal("100000"), "دلار", False),
    Quote("✴️ طلای ۱۸ عیار", "/en/gold-price/18ayar", "/en/gold-price", "18K Gold per Gram", Decimal("100000"), Decimal("100000000000")),
    Quote("✴️ نفت برنت", "/en/energy/brent-oil", "/en/energy", "Brent Crude Oil", Decimal("10"), Decimal("1000"), "دلار/بشکه", False),
    Quote("✴️ بیت کوین", "/en/crypto-price/btc", "/en/crypto-price", "Bitcoin (BTC)", Decimal("1000"), Decimal("10000000"), "دلار", False),
    Quote("✴️ تتر", "/en/crypto-price/usdt", "/en/crypto-price", "Tether (USDT)", Decimal("1000"), Decimal("1000000000")),
)


def acceptable(value: Decimal | None, quote: Quote) -> bool:
    return value is not None and quote.minimum <= value <= quote.maximum


def price_in_text(text: str, quote: Quote) -> Decimal | None:
    """Read a price from a card's own text, not from its whole surrounding page."""
    normalized = (text or "").translate(DIGIT_TRANSLATION)
    # A Bitcoin card can contain both IRR and USD; USD is the requested price.
    if quote.path.endswith("/btc"):
        match = re.search(r"(?:Price\s*\(USD\)\s*\$?|\$)\s*(" + NUM + ")", normalized, re.I)
        if match:
            amount = Decimal(match.group(1).replace(",", ""))
            if acceptable(amount, quote):
                return amount
        # If the card explicitly shows an IRR price but no USD, do not treat
        # an unrelated 24h percentage, market rank, or volume as a USD price.
        if "IRR" in normalized.upper():
            return None
    for amount in numbers_in(normalized):
        if acceptable(amount, quote):
            return amount
    return None


class AlanChandScraper:
    """Scrapes cards *and* tables, with detail pages as a last resort."""

    TARGET_URL: Final = BASE_URL + "/en"
    BASE_DIR: Final = Path(__file__).resolve().parent
    FILE_PATH: Final = OUTPUT_FILE
    CHANNEL_HANDLE: Final = "@CurrencyTel"

    def __init__(self, driver) -> None:
        self.driver = driver
        self.wait = WebDriverWait(driver, WAIT_SECONDS)

    def visit(self, path: str) -> bool:
        """A page that will not load is logged, not fatal to the other prices."""
        try:
            self.driver.get(BASE_URL + path)
            self.wait.until(lambda d: bool(d.find_elements(By.TAG_NAME, "main")))
            logger.info("Loaded %s", path)
            return True
        except (TimeoutException, WebDriverException) as exc:
            logger.warning("Page unavailable %s: %s", path, type(exc).__name__)
            return False

    @staticmethod
    def _row_value(link, quote: Quote) -> Decimal | None:
        try:
            for row in link.find_elements(By.XPATH, "ancestor::tr[1]"):
                cells = row.find_elements(By.XPATH, "./td")
                # Currency, gold and Tether: price (IRR) in column 2;
                # Bitcoin: price (USD) in column 4 on crypto tables.
                index = 3 if quote.path.endswith("/btc") else 1
                if len(cells) > index:
                    # A *price cell* should have just one market value.
                    value = price_in_text(cells[index].text, quote)
                    if acceptable(value, quote):
                        return value
        except WebDriverException:
            pass
        return None

    @staticmethod
    def _card_value(link, quote: Quote) -> Decimal | None:
        # The new AlanChand page uses both <a> cards and <tr> rows.
        try:
            value = price_in_text(link.text, quote)
            if acceptable(value, quote):
                return value
            # Some layouts put the price *next to* the anchor rather than in it.
            for xpath in ("..", "../.."):
                parents = link.find_elements(By.XPATH, xpath)
                if not parents:
                    continue
                text = parents[0].text
                if not (0 < len(text) < 350):
                    continue
                if quote.heading.split(" (")[0].casefold() not in text.casefold():
                    continue
                value = price_in_text(text, quote)
                if acceptable(value, quote):
                    return value
        except WebDriverException:
            pass
        return None

    def collect(self, needed: tuple[Quote, ...]) -> dict[str, Decimal]:
        wanted = {q.path: q for q in needed}
        results: dict[str, Decimal] = {}
        links = self.driver.find_elements(By.XPATH, "//main//a[@href]")
        for link in links:
            try:
                path = urlparse(link.get_attribute("href") or "").path.rstrip("/")
            except WebDriverException:
                continue
            quote = wanted.get(path)
            if quote is None or path in results:
                continue
            amount = self._row_value(link, quote)
            if amount is None:
                amount = self._card_value(link, quote)
            if acceptable(amount, quote):
                results[path] = amount / 10 if quote.in_rials else amount
        return results

    def detail(self, quote: Quote) -> Decimal | None:
        """Extract the *sell* quote from the asset detail page, never the buy quote.

        Currency detail pages no longer have a standalone "Swiss Franc" heading
        adjacent to the value. They show "Sell rate for CHF to IRR" followed by
        "3,246,000 IRR".  The old exact-name parser skipped that value.
        """
        try:
            lines = [
                x.strip()
                for x in self.driver.find_element(By.TAG_NAME, "main").text.splitlines()
                if x.strip()
            ]
        except WebDriverException:
            return None

        if quote.path.endswith("/btc"):
            content = " ".join(lines[:70])
            match = re.search(r"Price\s*\(USD\)\s*\$?\s*(" + NUM + ")", content, re.I)
            if match:
                amount = Decimal(match.group(1).replace(",", ""))
                return amount if acceptable(amount, quote) else None
            return None

        # Explicitly target the SELL price, as the same page also has a BUY
        # price, daily highs/lows, percentages and a currency converter.
        if quote.section == "/en/currencies-price":
            symbol = quote.path.rsplit("/", 1)[-1].upper()
            sell_heading = re.compile(
                rf"\bSell\s+(?:rate|price)\s+for\s+{re.escape(symbol)}\s+to\s+IRR\b",
                re.I,
            )
            price_line = re.compile(r"^\s*(" + NUM + r")\s*(?:IRR|Rials?)?\s*$", re.I)
            for i, line in enumerate(lines):
                if not sell_heading.search(line):
                    continue
                # Value appears directly after the sell heading; never scan
                # into the following 'Buy rate' section.
                for candidate in lines[i + 1 : i + 6]:
                    if re.search(r"\bBuy\s+(?:rate|price)\b", candidate, re.I):
                        break
                    match = price_line.fullmatch(candidate)
                    if not match:
                        continue
                    amount = Decimal(match.group(1).replace(",", ""))
                    if acceptable(amount, quote):
                        return amount / 10  # IRR -> Toman
                logger.warning("Sell price not found after heading: %s", quote.label)
                return None

        # Gold, coins, Brent, and fallback for non-standard detail layouts:
        # take only a numeric line immediately after an exact asset name.
        heading = quote.heading.casefold()
        for i, line in enumerate(lines):
            if line.casefold() != heading:
                continue
            for after in lines[i + 1 : i + 4]:
                if not re.match(r"^\s*[\d۰-۹٠-٩]", after):
                    continue
                value = price_in_text(after, quote)
                if acceptable(value, quote):
                    return value / 10 if quote.in_rials else value
        return None

    def build_report(self) -> str:
        found: dict[str, Decimal] = {}
        if self.visit("/en"):
            found.update(self.collect(Q))
            logger.info("Homepage: %s/%s prices retrieved", len(found), len(Q))

        # When only 1-2 prices are missing, directly visit their detail pages.
        # On GitHub runners the currency *listing* intermittently times out;
        # visiting it first only wastes 12 seconds and does not help CHF.
        attempted_detail: set[str] = set()
        initially_missing = [q for q in Q if q.path not in found]
        if 0 < len(initially_missing) <= 2:
            for quote in initially_missing:
                attempted_detail.add(quote.path)
                logger.info("Checking individual price page: %s", quote.path)
                if self.visit(quote.path):
                    value = self.detail(quote)
                    if acceptable(value * 10 if quote.in_rials and value is not None else value, quote):
                        found[quote.path] = value
                        logger.info("Recovered %s from detail page", quote.label)

        # Never visit /en/energy: on some runners it returns an empty page.
        # Brent is on the homepage; if absent, visit its *detail* page directly.
        for page in ("/en/currencies-price", "/en/gold-price", "/en/crypto-price"):
            needed = tuple(q for q in Q if q.section == page and q.path not in found)
            if not needed:
                continue
            logger.info("Checking %s for %s missing prices", page, len(needed))
            if self.visit(page):
                found.update(self.collect(needed))

        for quote in Q:
            if quote.path in found or quote.path in attempted_detail:
                continue
            logger.info("Checking individual price page: %s", quote.path)
            if self.visit(quote.path):
                value = self.detail(quote)
                if acceptable(value * 10 if quote.in_rials and value is not None else value, quote):
                    found[quote.path] = value
                    logger.info("Recovered %s from detail page", quote.label)

        missing = [q.label for q in Q if q.path not in found]
        if missing:
            raise RuntimeError(
                "Price report incomplete (old report left intact). Missing: " + ", ".join(missing)
            )

        lines = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین", ""]
        for quote in Q:
            rendered = f"{fmt(found[quote.path])} {quote.unit}"
            lines.append(f"{quote.label}: {rendered}")
            logger.info("%s: %s", quote.label, rendered)
        lines.extend(["", f"🆔 {self.CHANNEL_HANDLE}"])
        return "\n".join(lines)

    def run(self) -> str:
        report = self.build_report()
        temporary = self.FILE_PATH.with_name(self.FILE_PATH.name + ".tmp")
        temporary.write_text(report, encoding="utf-8")
        os.replace(temporary, self.FILE_PATH)
        logger.info("Report saved: %s", self.FILE_PATH)
        return report


class TGJUScraper(AlanChandScraper):
    """Compatible with `from TelegramWebScraper import TGJUScraper, __webdriver__`."""


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    browser = __webdriver__()
    try:
        print(TGJUScraper(browser).run())
    finally:
        browser.quit()


if __name__ == "__main__":
    main()
