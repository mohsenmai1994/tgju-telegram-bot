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
    TARGET_URL: Final[str] = "https://bv.emofid.com/market/currency"
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
            ("☸️ دلار آمريکا", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[1]/div[3]/div[1]"),
            ("☸️ یورو", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[2]/div[3]/div[1]"),
            ("☸️ پوند انگلیس", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[4]/div[3]/div[1]"),
            ("☸️ لیر ترکیه", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[5]/div[3]/div[1]"),
            ("☸️ فرانک سوئیس", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[10]/div[3]/div[1]"),
            ("☸️ یوان چین", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[6]/div[3]/div[1]"),
            ("☸️ ین ژاپن", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[7]/div[3]/div[1]"),
            ]

        # Coin values
        coins: List[tuple[str, str]] = [
            ("✴️ سکه بهار آزادی", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[3]/div[3]/div[1]"),
            ("✴️ نیم سکه", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[4]/div[3]/div[1]"),
            ("✴️ ربع سکه", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[5]/div[3]/div[1]"),
            ("✴️ سکه گرمی", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[6]/div[3]/div[1]"),
        ]

        # Gold and ounce values
        golds: List[tuple[str, str, str]] = [
            ("✴️ انس طلا", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[1]/div[3]/div[1]", "دلار"),
            ("✴️ طلای 18 عیار", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[7]/div[3]/div[1]", "ریال"),
        ]

        lines: list[str] = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین \n"]

        time.sleep(5)
        # Extract currencies
        for label, xpath in currencies:
            val = self.driver.find_element(By.XPATH, xpath).text.strip()
            lines.append(f"{label}: {val} ریال")
                
        time.sleep(2)
        self.driver.find_element(By.XPATH, "/html/body/app-root/div/main/ng-component/main/ng-component/header/div/a[2]").click()

        # Extract coins
        for label, xpath in coins:
            val = self.driver.find_element(By.XPATH, xpath).text.strip()
            lines.append(f"{label}: {val} ریال")

        # Extract gold
        for label, xpath, unit in golds:
            val = self.driver.find_element(By.XPATH, xpath).text.strip()
            lines.append(f"{label}: {val} {unit}")
                
        time.sleep(2)
        self.driver.find_element(By.XPATH, "/html/body/app-root/div/main/ng-component/main/ng-component/header/div/a[3]").click()
        
        # Extract bitcoin
        
        btc_val = self.driver.find_element(By.XPATH, "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[1]/div[3]/div[1]").text.strip()
        lines.append(f"✴️ بیت کوین: {btc_val} دلار")



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
