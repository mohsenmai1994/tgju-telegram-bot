from __future__ import annotations

import logging
from pathlib import Path
from typing import Final, List, Optional
import time
from selenium.webdriver.common.by import By
from Scraper import __webdriver__

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("TGJU_Scraper")


class TGJUScraper:
    # Target website and output configuration
    TARGET_URL: Final[str] = "https://alanchand.com/en/currencies-price"
    BASE_DIR: Final[Path] = Path(__file__).parent
    FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"
    CHANNEL_HANDLE: Final[str] = "@aghayebazar_official"

    def __init__(self, driver) -> None:
        self.driver = driver

    def build_report(self) -> str:
        """
        Extract market data from the page directly without helper methods.
        If an element is missing, it defaults to '-'.
        """
        time.sleep(5)
        # Currency values
        currencies: List[tuple[str, str]] = [
            ("☸️ دلار آمريکا", "/html/body/main/section[2]/div/div[1]/table/tbody/tr[1]/td[3]"),
            ("☸️ یورو", "/html/body/main/section[2]/div/div[1]/table/tbody/tr[2]/td[3]"),
            ("☸️ پوند انگلیس", "/html/body/main/section[2]/div/div[1]/table/tbody/tr[5]/td[3]"),
            ("☸️ لیر ترکیه", "/html/body/main/section[2]/div/div[1]/table/tbody/tr[4]/td[3]"),
            ("☸️ فرانک سوئیس", "/html/body/main/section[2]/div/div[2]/table/tbody/tr[1]/td[3]"),
            ("☸️ یوان چین", "/html/body/main/section[2]/div/div[1]/table/tbody/tr[6]/td[3]")
          
            ]

        # Coin values
        coins: List[tuple[str, str]] = [
            ("✴️ سکه بهار آزادی", "/html/body/main/section[1]/table/tbody/tr[4]/td[2]/text()"),
            ("✴️ نیم سکه", "/html/body/main/section[1]/table/tbody/tr[4]/td[3]/text()"),
            ("✴️ ربع سکه", "/html/body/main/section[1]/table/tbody/tr[6]/td[2]/text()")
            
        ]

        # Gold and ounce values
        golds: List[tuple[str, str, str]] = [
            ("✴️ انس طلا", "/html/body/main/section[1]/table/tbody/tr[8]/td[2]/text()", ""),
            ("✴️ طلای 18 عیار", "/html/body/main/section[1]/table/tbody/tr[2]/td[2]/text()]", "ریال")
        ]

        lines: list[str] = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین \n"]

        time.sleep(5)
        # Extract currencies
        for label, xpath in currencies:
            val = self.driver.find_element(By.XPATH, xpath).text.strip()
            lines.append(f"{label}: {val} ریال")

        
        self.driver.find_element(By.XPATH, "/html/body/header/div/div/div[1]/nav/a[3]").click()
        time.sleep(5)


        # Extract coins
        for label, xpath in coins:
            val = self.driver.find_element(By.XPATH, xpath).text.strip()
            lines.append(f"{label}: {val} ریال")

        # Extract gold
        for label, xpath, unit in golds:
            val = self.driver.find_element(By.XPATH, xpath).text.strip()
            lines.append(f"{label}: {val} {unit}")

        
        self.driver.find_element(By.XPATH, "/html/body/header/div/div/div[1]/nav/a[2]").click()        
        time.sleep(5)
        # Extract bitcoin
        
        btc_val = self.driver.find_element(By.XPATH, "/html/body/main/div/div/div/table/tbody/tr[2]/td[3]/span[3]").text.strip()
        lines.append(f"✴️ بیت کوین: {btc_val} دلار")

        tether_val = self.driver.find_element(By.XPATH, "/html/body/main/div/div/div/table/tbody/tr[1]/td[2]/span[1]").text.strip()
        lines.append(f"✴️ تتر : {tether_val} ریال")



        lines.append(f"\n🆔 {self.CHANNEL_HANDLE}")
        return "\n".join(lines)

    def run(self) -> Optional[str]:
        """
        Open target page and build report immediately.
        """
        self.driver.get(self.TARGET_URL)
        return self.build_report()

browser = __webdriver__()
scraper = TGJUScraper(browser)
content = scraper.run()

print(content)
