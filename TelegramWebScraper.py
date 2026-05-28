from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final, List, Optional

from selenium.webdriver.common.by import By
from Scraper import __webdriver__

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("TGJU_XPATH_Scraper")


# ----------------------------------------------
# داده‌های ثابت
# ----------------------------------------------
@dataclass(frozen=True)
class Asset:
    name: str
    xpath: str
    unit: str
    emoji: str


class TGJUScraper:
    TARGET_URL: Final[str] = "https://www.tgju.org/"
    BASE_DIR: Final[Path] = Path(__file__).parent
    FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"
    CHANNEL_HANDLE: Final[str] = "@aghayebazar_official"

    # عناصر اصلی با XPath
    ASSETS: Final[List[Asset]] = [
        Asset("دلار", '//*[@id="l-price_dollar_rl"]/span[1]', "ریال", "💵"),
        Asset("یورو", '//*[@id="l-price_eur"]/span[1]', "ریال", "💶"),
        Asset("درهم", '//*[@id="l-price_aed"]/span[1]', "ریال", "💵"),
        Asset("سکه امامی", '//*[@id="l-coin_sekee"]/span[1]', "ریال", "🟡"),
        Asset("نیم سکه", '//*[@id="l-coin_nim"]/span[1]', "ریال", "🟡"),
        Asset("ربع سکه", '//*[@id="l-coin_rob"]/span[1]', "ریال", "🟡"),
        Asset("طلای 18 عیار", '//*[@id="l-geram18"]/span[1]', "ریال", "🟡"),
        Asset("انس طلا", '//*[@id="l-ons"]/span[1]', "دلار", "🟡"),
        Asset("تتر", '//*[@id="l-usdt"]/span[1]', "ریال", "🪙"),
        Asset("بیت کوین", '//*[@id="l-btc"]/span[1]', "دلار", "🪙"),
    ]

    def __init__(self, driver) -> None:
        self.driver = driver

    # فانکشن خواندن xpath
    def read_xpath(self, xpath: str) -> str:
        try:
            el = self.driver.find_element(By.XPATH, xpath)
            return el.text.strip()
        except:
            return "N/A"

    def build_report(self) -> str:
        lines = ["#نرخ_ارز #سکه #طلا #کریپتو", ""]

        for asset in self.ASSETS:
            val = self.read_xpath(asset.xpath)
            lines.append(f"{asset.emoji} {asset.name}: {val} {asset.unit}")

        lines.append("")
        lines.append(f"ID: {self.CHANNEL_HANDLE}")

        return "\n".join(lines)

    def run(self) -> Optional[str]:
        try:
            logger.info(f"Opening {self.TARGET_URL}")
            self.driver.get(self.TARGET_URL)
            self.driver.implicitly_wait(10)

            report = self.build_report()
            self.FILE_PATH.write_text(report, encoding="utf-8")

            logger.info("Scrape completed successfully.")
            return report
        except Exception as exc:
            logger.error(f"Scraping failed: {exc}")
            return None


if __name__ == "__main__":
    browser = __webdriver__()
    try:
        scraper = TGJUScraper(browser)
        print(scraper.run())
    finally:
        browser.quit()
