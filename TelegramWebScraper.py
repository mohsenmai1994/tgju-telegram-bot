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
    TARGET_URL: Final[str] = "https://www.tgju.org/"
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
            ("☸️ دلار آمريکا", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[1]/td[1]"),
            ("☸️ یورو", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[2]/td[1]"),
            ("☸️ درهم آمارات", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[3]/td[1]"),
            ("☸️ پوند انگلیس", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[4]/td[1]"),
            ("☸️ لیر ترکیه", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[5]/td[1]"),
            ("☸️ فرانک سوئیس", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[6]/td[1]"),
            ("☸️ یوان چین", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[7]/td[1]"),
            ("☸️ ین ژاپن", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[8]/td[1]"),
            ("☸️ وون کره جنوبی", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[9]/td[1]"),
            ("☸️ دلار کانادا", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[10]/td[1]"),
            ("☸️ دلار استرالیا", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[11]/td[1]"),
            ("☸️ دلار نیوزلند", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[12]/td[1]"),
        ]

        # Coin values
        coins: List[tuple[str, str]] = [
            ("✴️ سکه بهار آزادی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[2]/td[1]"),
            ("✴️ نیم سکه", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[3]/td[1]"),
            ("✴️ ربع سکه", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[4]/td[1]"),
            ("✴️ سکه گرمی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[5]/td[1]"),
        ]

        # Gold and ounce values
        golds: List[tuple[str, str, str]] = [
            ("✴️ انس طلا", "/html/body/main/div[4]/div[3]/div[1]/table/tbody/tr[1]/td[1]", "دلار"),
            ("✴️ طلای 18 عیار", "/html/body/main/div[1]/div[2]/div/ul/li[5]/span[1]/span", "ریال"),
            ("✴️ طلای 24 عیار", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[2]/td[1]", "ریال"),
            ("✴️ طلای دست دوم", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[3]/td[1]", "ریال"),
        ]

        lines: list[str] = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین"]

        # Extract currencies
        for label, xpath in currencies:
            try:
                val = self.driver.find_element(By.XPATH, xpath).text.strip()
                lines.append(f"{label}: {val if val else '-'} ریال")
            except Exception:
                lines.append(f"{label}: - ریال")

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

        # Extract tether and bitcoin
        try:
            tether_val = self.driver.find_element(By.XPATH, "/html/body/main/div[8]/div/div/div[1]/div[2]/table/tbody/tr[5]/td[1]").text.strip()
            lines.append(f"✴️ تتر: {tether_val if tether_val else '-'} ریال")
        except Exception:
            lines.append("✴️ تتر: - ریال")

        try:
            btc_val = self.driver.find_element(By.XPATH, "/html/body/main/div[8]/div/div/div[1]/div[2]/table/tbody/tr[1]/td[2]").text.strip()
            lines.append(f"✴️ بیت کوین: {btc_val if btc_val else '-'} دلار")
        except Exception:
            lines.append("✴️ بیت کوین: - دلار")

        # Add market time
        if market_time != "N/A":
            lines.append(f"📅 {market_time}")

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
