from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Final, List, Optional
import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from Scraper import __webdriver__


# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("TGJU_Scraper")


def clean_number(text: str) -> str:
    """
    Keep digits and thousand separators.
    Converts Persian digits to English.
    """

    if not text:
        return "-"

    # Persian → English digits
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    for i, d in enumerate(persian_digits):
        text = text.replace(d, str(i))

    # unify thousand separator
    text = text.replace("٬", ",")

    # keep only digits and comma
    return re.sub(r"[^\d,]", "", text)



class TGJUScraper:
    TARGET_URL: Final[str] = "https://alanchand.com/en/currencies-price"
    BASE_DIR: Final[Path] = Path(__file__).parent
    FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"
    CHANNEL_HANDLE: Final[str] = "@aghayebazar_official"

    def __init__(self, driver) -> None:
        self.driver = driver

    def get_value(self, xpath: str) -> str:
        """Safely get and clean number from page"""
        try:
            raw = self.driver.find_element(By.XPATH, xpath).text.strip()
            return clean_number(raw)
        except NoSuchElementException:
            logger.warning(f"Element not found: {xpath}")
            return "-"

    def build_report(self) -> str:
        time.sleep(5)

        currencies: List[tuple[str, str]] = [
            ("☸️ دلار آمريکا", "/html/body/main/section[2]/div/div[1]/table/tbody/tr[1]/td[3]"),
            ("☸️ یورو", "/html/body/main/section[2]/div/div[1]/table/tbody/tr[2]/td[3]"),
            ("☸️ پوند انگلیس", "/html/body/main/section[2]/div/div[1]/table/tbody/tr[5]/td[3]"),
            ("☸️ لیر ترکیه", "/html/body/main/section[2]/div/div[1]/table/tbody/tr[4]/td[3]"),
            ("☸️ فرانک سوئیس", "/html/body/main/section[2]/div/div[2]/table/tbody/tr[1]/td[3]"),
            ("☸️ یوان چین", "/html/body/main/section[2]/div/div[1]/table/tbody/tr[6]/td[3]")
        ]

        coins: List[tuple[str, str]] = [
            ("✴️ سکه بهار آزادی", "/html/body/main/section[1]/table/tbody/tr[4]/td[2]"),
            ("✴️ نیم سکه", "/html/body/main/section[1]/table/tbody/tr[4]/td[3]"),
            ("✴️ ربع سکه", "/html/body/main/section[1]/table/tbody/tr[6]/td[2]")
        ]

        golds: List[tuple[str, str, str]] = [
            ("✴️ انس طلا", "/html/body/main/section/table/tbody/tr[8]/td[2]", ""),
            ("✴️ طلای 18 عیار", "/html/body/main/section[1]/table/tbody/tr[2]/td[2]", "تومان")
        ]

        lines: list[str] = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین \n"]

        time.sleep(5)

        # Currencies
        for label, xpath in currencies:
            val = self.get_value(xpath)
            lines.append(f"{label}: {val} تومان")

        # Go to coins page
        self.driver.find_element(By.XPATH, "/html/body/header/div/div/div[1]/nav/a[3]").click()
        time.sleep(5)

        # Coins
        for label, xpath in coins:
            val = self.get_value(xpath)
            lines.append(f"{label}: {val} تومان")

        # Gold
        for label, xpath, unit in golds:
            val = self.get_value(xpath)
            lines.append(f"{label}: {val} {unit}")

        # Go to crypto page
        self.driver.find_element(By.XPATH, "/html/body/header/div/div/div[1]/nav/a[2]").click()
        time.sleep(5)

        # Bitcoin
        btc_val = self.get_value("/html/body/main/div/div/div/table/tbody/tr[2]/td[3]/span[3]")
        lines.append(f"✴️ بیت کوین: {btc_val} دلار")

        # Tether
        tether_val = self.get_value("/html/body/main/div/div/div/table/tbody/tr[1]/td[2]/span[1]")
        lines.append(f"✴️ تتر : {tether_val} تومان")

        lines.append(f"\n🆔 {self.CHANNEL_HANDLE}")

        return "\n".join(lines)

    def run(self) -> Optional[str]:
        self.driver.get(self.TARGET_URL)
        return self.build_report()


browser = __webdriver__()
scraper = TGJUScraper(browser)
content = scraper.run()

print(content)
