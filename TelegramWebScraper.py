from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final, List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from Scraper import __webdriver__

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("TGJU_Scraper")


@dataclass(frozen=True)
class AssetMetadata:
    search_keys: tuple[str, ...]
    label: str
    emoji: str
    unit: str


class TGJUScraper:
    TARGET_URL: Final[str] = "https://www.tgju.org/"
    BASE_DIR: Final[Path] = Path(__file__).parent
    FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"
    CHANNEL_HANDLE: Final[str] = "@aghayebazar_official"

    def __init__(self, driver) -> None:
        self.driver = driver

    def _safe_text(self, xpath: str, default: str = "N/A") -> str:
        try:
            text = self.driver.find_element(By.XPATH, xpath).text.strip()
            return text if text else default
        except Exception:
            return default

    def _wait_for_page_ready(self, timeout: int = 25) -> None:
        """
        Wait until *key* dynamic values are actually populated (not empty / not '-').
        This is stronger than implicit waits and is a practical "page is ready" signal
        for JS-driven pages like tgju.org.
        """
        wait = WebDriverWait(self.driver, timeout)

        # 1) Timestamp exists and is not empty
        wait.until(
            lambda d: d.find_element(
                By.XPATH, "/html/body/div[2]/header/div[4]/div[2]/div[2]/div/span"
            ).text.strip() != ""
        )

        # 2) One major currency cell has real text (USD row)
        wait.until(
            lambda d: d.find_element(
                By.XPATH,
                "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[1]/td[1]",
            ).text.strip() not in ("", "-")
        )

        # 3) One major coin cell has real text (Emami)
        wait.until(
            lambda d: d.find_element(
                By.XPATH,
                "/html/body/main/div[4]/div[4]/div[10]/table/tbody/tr[1]/td[1]",
            ).text.strip() not in ("", "-")
        )

        # 4) Gold ounce cell has real text
        wait.until(
            lambda d: d.find_element(
                By.XPATH,
                "/html/body/main/div[4]/div[3]/div[1]/table/tbody/tr[1]/td[1]",
            ).text.strip() not in ("", "-")
        )

    def build_report(self) -> str:
        market_time = self._safe_text(
            "/html/body/div[2]/header/div[4]/div[2]/div[2]/div/span",
            "N/A",
        )

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

        coins: List[tuple[str, str]] = [
            ("✴️ سکه امامی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[1]/td[1]"),
            ("✴️ سکه بهار آزادی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[2]/td[1]"),
            ("✴️ نیم سکه", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[3]/td[1]"),
            ("✴️ ربع سکه", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[4]/td[1]"),
            ("✴️ سکه گرمی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[5]/td[1]"),
        ]

        golds: List[tuple[str, str, str]] = [
            ("✴️ انس طلا", "/html/body/main/div[4]/div[3]/div[1]/table/tbody/tr[1]/td[1]", "دلار"),
            ("✴️ طلای 18 عیار", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[1]/td[1]", "ریال"),
            ("✴️ طلای 24 عیار", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[2]/td[1]", "ریال"),
            ("✴️ طلای دست دوم", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[3]/td[1]", "ریال"),
        ]

        tether_xpath = "/html/body/main/div[8]/div/div/div[1]/div[2]/table/tbody/tr[5]/td[1]"
        bitcoin_xpath = "/html/body/main/div[8]/div/div/div[1]/div[2]/table/tbody/tr[1]/td[2]"

        lines: list[str] = []
        lines.append("#نرخ_ارز #سکه #طلا #دلار #بیتکوین")

        for label, xpath in currencies:
            value = self._safe_text(xpath, "-")
            lines.append(f"{label}: {value} ریال")

        for label, xpath in coins:
            value = self._safe_text(xpath, "-")
            lines.append(f"{label}: {value} ریال")

        for label, xpath, unit in golds:
            value = self._safe_text(xpath, "-")
            lines.append(f"{label}: {value} {unit}")

        tether_value = self._safe_text(tether_xpath, "-")
        lines.append(f"✴️ تتر: {tether_value} ریال")

        bitcoin_value = self._safe_text(bitcoin_xpath, "-")
        lines.append(f"✴️ بیت کوین: {bitcoin_value} دلار")

        lines.append(market_time)
        lines.append(f"ID: {self.CHANNEL_HANDLE}")

        return "\n".join(lines)

    def run(self) -> Optional[str]:
        try:
            self.driver.get(self.TARGET_URL)

            # Replace implicit wait with explicit readiness checks for JS-populated tables.
            self._wait_for_page_ready(timeout=25)

            report = self.build_report()

            with open(self.FILE_PATH, "w", encoding="utf-8") as f:
                f.write(report)

            logger.info("Report saved to market_log.txt")
            return report

        except Exception as exc:
            logger.exception(f"Scraper failed: {exc}")
            return None

