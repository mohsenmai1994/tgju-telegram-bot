from __future__ import annotations

import logging
from pathlib import Path
from typing import Final, Optional

from selenium.webdriver.common.by import By
from Scraper import __webdriver__

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("TGJU_Scraper")


class TGJUScraper:
    TARGET_URL: Final[str] = "https://www.tgju.org/"
    BASE_DIR: Final[Path] = Path(__file__).parent
    FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"

    def __init__(self, driver) -> None:
        self.driver = driver

    def _safe_text(self, xpath: str, default: str = "") -> str:
        try:
            return self.driver.find_element(By.XPATH, xpath).text.strip()
        except Exception:
            return default

    def build_report(self) -> str:
        # market time
        market_time = self._safe_text(
            "/html/body/div[2]/header/div[4]/div[2]/div[2]/div/span",
            "N/A"
        )

        # currencies
        currencies = [
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

        # coins
        coins = [
            ("✴️ سکه امامی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[1]/td[1]"),
            ("✴️ سکه بهار آزادی", "/html/body/main/div[4]/div[4]/div[10]/table/tbody/tr[2]/td[1]"),
            ("✴️ نیم سکه", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[3]/td[1]"),
            ("✴️ ربع سکه", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[4]/td[1]"),
            ("✴️ سکه گرمی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[5]/td[1]"),
        ]

        # gold
        golds = [
            ("✴️ انس طلا", "/html/body/main/div[1]/div[2]/div/ul/li[2]/span[1]/span", "دلار"),
            ("✴️ طلای 18 عیار", "/html/body/main/div[1]/div[2]/div/ul/li[4]/span[1]/span", "ریال"),
            ("✴️ طلای 24 عیار", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[2]/td[1]", "ریال"),
            ("✴️ طلای دست دوم", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[3]/td[1]", "ریال"),
        ]

        # crypto / dollar
        tether_xpath = "/html/body/main/div[8]/div/div/div[1]/div[2]/table/tbody/tr[5]/td[1]"
        bitcoin_xpath = "/html/body/main/div[8]/div/div/div[1]/div[2]/table/tbody/tr[1]/td[2]"

        lines = []
        lines.append("#نرخ_ارز #سکه #طلا #دلار #بیتکوین")
        lines.append("")

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

        lines.append("")
        lines.append(market_time)
        lines.append("ID: @aghayebazar_official")

        return "\n".join(lines)

    def run(self) -> Optional[str]:
        try:
            self.driver.get(self.TARGET_URL)
            self.driver.implicitly_wait(10)

            report = self.build_report()

            with open(self.FILE_PATH, "w", encoding="utf-8") as f:
                f.write(report)

            logger.info("Report saved to market_log.txt")
            return report
        except Exception as exc:
            logger.exception(f"Scraper failed: {exc}")
            return None
