from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Final, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
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
    DEBUG_SCREENSHOT: Final[Path] = BASE_DIR / "debug_screenshot.png"
    DEBUG_HTML: Final[Path] = BASE_DIR / "debug_page_source.html"

    def __init__(self, driver) -> None:
        self.driver = driver

    def _safe_text(self, xpath: str, default: str = "") -> str:
        try:
            text = self.driver.find_element(By.XPATH, xpath).text.strip()
            return text if text else default
        except Exception:
            return default

    def _contains_number(self, value: str) -> bool:
        if not value:
            return False
        return bool(re.search(r"\d", value))

    def _is_valid_price(self, value: str) -> bool:
        if not value:
            return False

        normalized = value.strip().replace(",", "").replace("٬", "").replace(" ", "")
        if normalized in {"", "-", "--", "---", "0", "0.0", "..."}:
            return False

        return self._contains_number(normalized)

    def _save_debug_artifacts(self) -> None:
        try:
            self.driver.save_screenshot(str(self.DEBUG_SCREENSHOT))
            logger.info("Debug screenshot saved: %s", self.DEBUG_SCREENSHOT)
        except Exception as exc:
            logger.warning("Failed to save screenshot: %s", exc)

        try:
            html = self.driver.page_source
            self.DEBUG_HTML.write_text(html, encoding="utf-8")
            logger.info("Debug HTML saved: %s", self.DEBUG_HTML)
        except Exception as exc:
            logger.warning("Failed to save HTML source: %s", exc)

    def _wait_for_page_ready(self, timeout: int = 40) -> bool:
        """
        روی GitHub ممکن است صفحه باز شود ولی داده واقعی هنوز sync نشده باشد.
        این متد چند فیلد کلیدی را چک می‌کند تا مطمئن شود داده واقعاً آمده.
        """
        important_xpaths = {
            "market_time": "/html/body/div[2]/header/div[4]/div[2]/div[2]/div/span",
            "usd": "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[1]/td[1]",
            "emami": "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[1]/td[1]",
            "ounce": "/html/body/main/div[1]/div[2]/div/ul/li[2]/span[1]/span",
            "bitcoin": "/html/body/main/div[8]/div/div/div[1]/div[2]/table/tbody/tr[1]/td[2]",
        }

        end_time = time.time() + timeout
        last_snapshot = {}

        while time.time() < end_time:
            snapshot = {
                key: self._safe_text(xpath, "")
                for key, xpath in important_xpaths.items()
            }
            last_snapshot = snapshot

            market_time_ok = snapshot["market_time"].strip() != ""
            usd_ok = self._is_valid_price(snapshot["usd"])
            emami_ok = self._is_valid_price(snapshot["emami"])
            ounce_ok = self._is_valid_price(snapshot["ounce"])
            bitcoin_ok = self._is_valid_price(snapshot["bitcoin"])

            logger.info(
                "Readiness check | time=%r | usd=%r | emami=%r | ounce=%r | btc=%r",
                snapshot["market_time"],
                snapshot["usd"],
                snapshot["emami"],
                snapshot["ounce"],
                snapshot["bitcoin"],
            )

            if market_time_ok and usd_ok and emami_ok and ounce_ok and bitcoin_ok:
                logger.info("Dynamic data looks ready.")
                return True

            time.sleep(2)

        logger.warning("Timeout waiting for fresh dynamic data. Last snapshot: %s", last_snapshot)
        return False

    def _log_environment_hints(self) -> None:
        try:
            title = self.driver.title
        except Exception:
            title = "N/A"

        try:
            current_url = self.driver.current_url
        except Exception:
            current_url = "N/A"

        logger.info("Page title: %s", title)
        logger.info("Current URL: %s", current_url)

    def build_report(self) -> str:
        market_time = self._safe_text(
            "/html/body/div[2]/header/div[4]/div[2]/div[2]/div/span",
            "N/A"
        )

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

        coins = [
            ("✴️ سکه امامی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[1]/td[1]"),
            ("✴️ سکه بهار آزادی", "/html/body/main/div[4]/div[4]/div[10]/table/tbody/tr[2]/td[1]"),
            ("✴️ نیم سکه", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[3]/td[1]"),
            ("✴️ ربع سکه", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[4]/td[1]"),
            ("✴️ سکه گرمی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[5]/td[1]"),
        ]

        golds = [
            ("✴️ انس طلا", "/html/body/main/div[1]/div[2]/div/ul/li[2]/span[1]/span", "دلار"),
            ("✴️ طلای 18 عیار", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[1]/td[1]", "ریال"),
            ("✴️ طلای 24 عیار", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[2]/td[1]", "ریال"),
            ("✴️ طلای دست دوم", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[3]/td[1]", "ریال"),
        ]

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
            logger.info("Opening target URL: %s", self.TARGET_URL)
            self.driver.get(self.TARGET_URL)

            # کمی مکث اولیه برای استیبل شدن DOM
            time.sleep(3)

            self._log_environment_hints()

            ready = self._wait_for_page_ready(timeout=40)

            # همیشه برای دیباگ در محیط‌هایی مثل GitHub آرتیفکت ذخیره کن
            self._save_debug_artifacts()

            if not ready:
                logger.warning("Page did not look fully fresh, but build_report() will still run.")

            report = self.build_report()

            with open(self.FILE_PATH, "w", encoding="utf-8") as f:
                f.write(report)

            logger.info("Report saved to market_log.txt")
            return report

        except Exception as exc:
            logger.exception("Scraper failed: %s", exc)
            self._save_debug_artifacts()
            return None


if __name__ == "__main__":
    browser = __webdriver__()
    try:
        scraper = TGJUScraper(browser)
        print(scraper.run())
    finally:
        browser.quit()
