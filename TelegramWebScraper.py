from __future__ import annotations
import logging
from pathlib import Path
from typing import Final, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Scraper import __webdriver__

# تنظیمات لاگ برای مانیتورینگ در گیت‌هاب
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("TGJU_Scraper")

class TGJUScraper:
    TARGET_URL: Final[str] = "https://www.tgju.org/"
    FILE_PATH: Final[Path] = Path(__file__).parent / "market_log.txt"
    CHANNEL_HANDLE: Final[str] = "@aghayebazar_official"

    def __init__(self, driver) -> None:
        self.driver = driver

    def _safe_text(self, xpath: str, default: str = "-") -> str:
        """استخراج امن متن با مدیریت خطا"""
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            text = element.text.strip()
            return text if text and text != "0" else default
        except:
            return default

    def _wait_for_sync(self, timeout: int = 30):
        """
        حیاتی‌ترین بخش برای گیت‌هاب: 
        منتظر می‌ماند تا قیمت دلار (اولین سطر جدول) از حالت لودینگ یا مقدار خالی خارج شود.
        """
        logger.info("Waiting for dynamic data to sync...")
        wait = WebDriverWait(self.driver, timeout)
        # چک کردن اینکه آیا قیمت دلار در جدول ظاهر شده و خالی نیست
        usd_xpath = "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[1]/td[1]"
        wait.until(lambda d: d.find_element(By.XPATH, usd_xpath).text.strip() not in ["", "0", "-", "..."])
        logger.info("Data synced successfully.")

    def build_report(self) -> str:
        # استخراج زمان به‌روزرسانی سایت
        market_time = self._safe_text("/html/body/div[2]/header/div[4]/div[2]/div[2]/div/span", "N/A")

        # ساختار داده‌ها (دقیقاً طبق ستون اول جداول سایت)
        currencies = [
            ("☸️ دلار آمريكا", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[1]/td[1]"),
            ("☸️ یورو", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[2]/td[1]"),
            ("☸️ درهم امارات", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[3]/td[1]"),
            ("☸️ پوند انگلیس", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[4]/td[1]"),
            ("☸️ لیر ترکیه", "/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody//tr[5]/td[1]"),
        ]

        coins = [
            ("✴️ سکه امامی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[1]/td[1]"),
            ("✴️ سکه بهار آزادی", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[2]/td[1]"),
            ("✴️ نیم سکه", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[3]/td[1]"),
            ("✴️ ربع سکه", "/html/body/main/div[4]/div[4]/div[13]/table/tbody/tr[4]/td[1]"),
        ]

        gold_items = [
            ("✴️ انس طلا", "/html/body/main/div[4]/div[3]/div[1]/table/tbody/tr[1]/td[1]", "دلار"),
            ("✴️ طلای 18 عیار", "/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr[1]/td[1]", "ریال"),
        ]

        # تتر و بیت‌کوین از بخش کریپتو
        tether = self._safe_text("/html/body/main/div[8]/div/div/div[1]/div[2]/table/tbody/tr[5]/td[1]")
        bitcoin = self._safe_text("/html/body/main/div[8]/div/div/div[1]/div[2]/table/tbody/tr[1]/td[2]")

        # قالب‌بندی نهایی خروجی
        lines = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین"]
        for label, xpath in currencies: lines.append(f"{label}: {self._safe_text(xpath)} ریال")
        for label, xpath in coins: lines.append(f"{label}: {self._safe_text(xpath)} ریال")
        for label, xpath, unit in gold_items: lines.append(f"{label}: {self._safe_text(xpath)} {unit}")
        
        lines.append(f"✴️ تتر: {tether} ریال")
        lines.append(f"✴️ بیت کوین: {bitcoin} دلار")
        lines.append(f"\n{market_time}")
        lines.append(f"ID: {self.CHANNEL_HANDLE}")

        return "\n".join(lines)

    def run(self) -> Optional[str]:
        try:
            logger.info(f"Opening {self.TARGET_URL}...")
            self.driver.get(self.TARGET_URL)
            
            # صبر فعال برای لود شدن داده‌های داینامیک
            self._wait_for_sync(timeout=35)

            report = self.build_report()
            with open(self.FILE_PATH, "w", encoding="utf-8") as f:
                f.write(report)
            
            logger.info("Update complete. market_log.txt updated.")
            return report
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return None

if __name__ == "__main__":
    browser = __webdriver__()
    try:
        scraper = TGJUScraper(browser)
        print(scraper.run())
    finally:
        browser.quit()
