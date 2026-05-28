from __future__ import annotations

import logging
import time
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
    # Target website and channel configurations
    TARGET_URL: Final[str] = "https://www.tgju.org/"
    BASE_DIR: Final[Path] = Path(__file__).parent
    FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"
    CHANNEL_HANDLE: Final[str] = "@aghayebazar_official"

    def __init__(self, driver) -> None:
        self.driver = driver

    def _safe_text(self, xpath: str, default: str = "-") -> str:
        """
        Safely attempts to find an element and retrieve its stripped text content.
        Returns the default value if an exception occurs or if the element is empty.
        """
        try:
            text = self.driver.find_element(By.XPATH, xpath).text.strip()
            return text if text else default
        except Exception:
            return default

    def _wait_until_text_ready(
        self,
        xpath: str,
        timeout: float = 15.0,
        poll_interval: float = 0.3,
        invalid_values: tuple[str, ...] = ("", "-"),
    ) -> bool:
        """
        Smart poll-based wait. Keeps checking the given XPath until its text value
        is loaded (i.e., not empty and not matching any invalid fallback values).
        Returns True if the data loads successfully within the timeout, otherwise False.
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            current_value = self._safe_text(xpath, default="")
            if current_value.strip() not in invalid_values:
                return True
            time.sleep(poll_interval)
        return False

    def build_report(self) -> str:
        """
        Retrieves all live financial rates from the DOM and formats them
        into a clean, structured text report ready for Telegram.
        """
        # Retrieve the overall market update timestamp
        market_time = self._safe_text(
            "/html/body/div[2]/header/div[4]/div[2]/div[2]/div/span",
            "N/A",
        )

        # List of currencies to extract (Label, XPath)
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

        # List of physical gold coins to extract (Label, XPath)
        coins: List[tuple[str, str]] = [
            ("✴️ سکه بهار آزادی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[2]/td[1]"),
            ("✴️ نیم سکه", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[3]/td[1]"),
            ("✴️ ربع سکه", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[4]/td[1]"),
            ("✴️ سکه گرمی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[5]/td[1]"),
        ]

        # List of gold items and ounces (Label, XPath, Measurement Unit)
        golds: List[tuple[str, str, str]] = [
            ("✴️ انس طلا", "/html/body/main/div[4]/div[3]/div[1]/table/tbody/tr[1]/td[1]", "دلار"),
            ("✴️ طلای 18 عیار", "/html/body/main/div[1]/div[2]/div/ul/li[5]/span[1]/span", "ریال"),
            ("✴️ طلای 24 عیار", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[2]/td[1]", "ریال"),
            ("✴️ طلای دست دوم", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[3]/td[1]", "ریال"),
        ]

        # Target XPaths for crypto values
        tether_xpath = "/html/body/main/div[8]/div/div/div[1]/div[2]/table/tbody/tr[5]/td[1]"
        bitcoin_xpath = "/html/body/main/div[8]/div/div/div[1]/div[2]/table/tbody/tr[1]/td[2]"

        # Assemble the report lines
        lines: list[str] = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین"]

        # Append formatted currency values
        for label, xpath in currencies:
            lines.append(f"{label}: {self._safe_text(xpath)} ریال")

        # Append formatted gold coin values
        for label, xpath in coins:
            lines.append(f"{label}: {self._safe_text(xpath)} ریال")

        # Append formatted physical gold metrics
        for label, xpath, unit in golds:
            lines.append(f"{label}: {self._safe_text(xpath)} {unit}")

        # Append cryptocurrency metrics
        lines.append(f"✴️ تتر: {self._safe_text(tether_xpath)} ریال")
        lines.append(f"✴️ بیت کوین: {self._safe_text(bitcoin_xpath)} دلار")

        # Append the market update timestamp if valid
        if market_time != "N/A":
            lines.append(f"📅 {market_time}")

        # Append target telegram channel handle
        lines.append(f"🆔 {self.CHANNEL_HANDLE}")
        return "\n".join(lines)

    def run(self) -> Optional[str]:
        """
        Executes the main scraping process: navigates to the URL, awaits the
        appearance of key dynamic elements, and extracts the final structured report.
        """
        try:
            self.driver.get(self.TARGET_URL)

            # Smart wait: Ensure at least the first major currency (USD) is populated
            # from '-' to actual numeric text before compiling the report.
            usd_xpath = "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[1]/td[1]"
            self._wait_until_text_ready(usd_xpath, timeout=15.0, poll_interval=0.3)

            return self.build_report()
        except Exception as exc:
            logger.exception("Scraper failed: %s", exc)
            return None
