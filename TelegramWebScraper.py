from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Final, List, Optional

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from Scraper import __webdriver__


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("TGJU_Scraper")


def clean_number(text: str) -> str:
    if not text:
        return "-"

    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    for i, d in enumerate(persian_digits):
        text = text.replace(d, str(i))

    text = text.replace("٬", ",")
    return re.sub(r"[^\d,\.]", "", text)


class TGJUScraper:
    TARGET_URL: Final[str] = "https://alanchand.com/en/currencies-price"
    BASE_DIR: Final[Path] = Path(__file__).parent
    FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"
    CHANNEL_HANDLE: Final[str] = "@CurrencyTel"

    def __init__(self, driver) -> None:
        self.driver = driver

    def get_value(self, xpath: str) -> str:
        try:
            raw = self.driver.find_element(By.XPATH, xpath).text.strip()
            return clean_number(raw)
        except NoSuchElementException:
            logger.warning(f"Element not found: {xpath}")
            return "-"

    def build_report(self) -> str:
       currencies: List[tuple[str, str]] = [
            ("☸️ دلار آمریکا", "/html/body/main/div/div[2]/div/section[1]/div[2]/table/tbody/tr[1]/td[1]/b"),
            ("☸️ یورو", "/html/body/main/div/div[2]/div/section[1]/div[2]/table/tbody/tr[2]/td[1]/b"),
            ("☸️ پوند انگلیس", "/html/body/main/div/div[2]/div/section[1]/div[2]/table/tbody/tr[3]/td[1]/b"),
            ("☸️ لیر ترکیه", "/html/body/main/div/div[2]/div/section[1]/div[2]/table/tbody/tr[5]/td[1]/b"),
            ("☸️ فرانک سوئیس", "/html/body/main/div/div[2]/div/section[1]/div[2]/table/tbody/tr[24]/td[1]/b"),
            ("☸️ یوان چین", "/html/body/main/div/div[2]/div/section[1]/div[2]/table/tbody/tr[7]/td[1]/b")
        ]

        coins: List[tuple[str, str]] = [
            ("✴️ سکه بهار آزادی", "/html/body/main/div/section[3]/div[2]/a[3]/span[2]"),
            ("✴️ نیم سکه", "/html/body/main/div/div[3]/div/div[1]/div[2]/div[2]/a[3]/span[2]"),
            ("✴️ ربع سکه", "/html/body/main/div/section[3]/div[2]/a[1]/span[2]")
        ]

        golds: List[tuple[str, str, str]] = [
            ("✴️ انس طلا", "/html/body/main/div/section[1]/a[1]/span[2]", ""),
            ("✴️ طلای 18 عیار", "/html/body/main/div/section[1]/a[3]/span[2]", ""),
            ("✴️ نفت برنت", "/html/body/main/div/div[4]/div[1]/div[2]/div[2]/div[2]/a[1]/span[2]", "")
        ]

        lines: list[str] = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین \n"]

        for label, xpath in currencies:
            val = self.get_value(xpath)
            lines.append(f"{label}: {val}")

        self.driver.find_element(By.XPATH, "/html/body/header/div/a").click()

        for label, xpath in coins:
            val = self.get_value(xpath)
            lines.append(f"{label}: {val}")

        for label, xpath, unit in golds:
            val = self.get_value(xpath)
            lines.append(f"{label}: {val} {unit}")

        btc_val = self.get_value("/html/body/main/div/section[1]/a[8]/span[2]")
        lines.append(f"✴️ بیت کوین: {btc_val} دلار")

        tether_val = self.get_value("/html/body/main/div/section[3]/div[2]/a[5]/span[2]")
        lines.append(f"✴️ تتر : {tether_val}")

        lines.append(f"\n🆔 {self.CHANNEL_HANDLE}")

        return "\n".join(lines)

    def run(self) -> Optional[str]:
        self.driver.get(self.TARGET_URL)
        return self.build_report()


browser = __webdriver__()
scraper = TGJUScraper(browser)
content = scraper.run()

if content is not None:
    scraper.FILE_PATH.write_text(content, encoding="utf-8")
    logger.info("Report saved to %s", scraper.FILE_PATH)

print(content)
browser.quit()
