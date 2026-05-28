from __future__ import annotations

import logging
from pathlib import Path
from typing import Final, List, Optional

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
        # Read market update time from the header
        try:
            market_time_el = self.driver.find_element(By.XPATH, "/html/body/div[2]/header/div[4]/div[2]/div[2]/div/span")
            market_time = market_time_el.text.strip() if market_time_el.text.strip() else "N/A"
        except Exception:
            market_time = "N/A"

        # Currency values
        currencies: List[tuple[str, str]] = [
            ("☸️ دلار آمريکا", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[1]/div[3]/div[1]"),
            ("☸️ یورو", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[2]/div[3]/div[1]"),
            ("☸️ پوند انگلیس", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[4]/div[3]/div[1]"),
            ("☸️ لیر ترکیه", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[6]/div[3]/div[1]"),
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
            ("✴️ انس طلا", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[1]/div[3]/div[1]/span", "دلار"),
            ("✴️ طلای 18 عیار", "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[7]/div[3]/div[1]", "ریال"),
        ]

        lines: list[str] = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین \n"]

        # Extract currencies
        for label, xpath in currencies:
            try:
                val = self.driver.find_element(By.XPATH, xpath).text.strip()
                lines.append(f"{label}: {val if val else '-'} ریال")
            except Exception:
                lines.append(f"{label}: - ریال")

        self.driver.find_element(By.XPATH, "/html/body/app-root/div/main/ng-component/main/ng-component/header/div/a[2]").click()

        # Extract coins
        for label, xpath in coins:
            try:
                val = self.driver.find_element(By.XPATH, xpath).text.strip()
                lines.append(f"{label}: {val if val else '-'} ریال")
            except Exception:
                lines.append(f"{label}: - ریال")

        # Extract gold
        for label, xpath, unit in golds:
            try:
                val = self.driver.find_element(By.XPATH, xpath).text.strip()
                lines.append(f"{label}: {val if val else '-'} {unit}")
            except Exception:
                lines.append(f"{label}: - {unit}")
  
        self.driver.find_element(By.XPATH, "/html/body/app-root/div/main/ng-component/main/ng-component/header/div/a[3]").click()
        
        # Extract bitcoin
        
        try:
            btc_val = self.driver.find_element(By.XPATH, "/html/body/app-root/div/main/ng-component/main/ng-component/main/div/div[3]/div/div/div[1]/div[3]/div[1]").text.strip()
            lines.append(f"✴️ بیت کوین: {btc_val if btc_val else '-'} دلار")
        except Exception:
            lines.append("✴️ بیت کوین: - دلار")

        # Add market time
        if market_time != "N/A":
            lines.append(f"\n {market_time}")

        lines.append(f"🆔 {self.CHANNEL_HANDLE}")
        return "\n".join(lines)

    def run(self) -> Optional[str]:
        """
        Open target page and build report immediately.
        """
        try:
            self.driver.get(self.TARGET_URL)
            return self.build_report()
        except Exception as exc:
            logger.exception("Scraper failed: %s", exc)
            return None

browser = __webdriver__()
scraper = TGJUScraper(browser)
content = scraper.run()

print(content)
