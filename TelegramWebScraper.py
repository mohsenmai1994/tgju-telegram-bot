from __future__ import annotations
import logging
import time
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

    def __init__(self, driver: __webdriver__) -> None:
        self.driver = driver

    def _get_val(self, xpath: str) -> str:
        try:
            # استفاده از متد سفارشی شما که در Scraper.py تعریف کردید
            element = self.driver.find_element(By.XPATH, xpath)
            return element.text.strip()
        except Exception:
            return "-"

    def build_report(self) -> str:
        # زمان بروزرسانی از هدر سایت
        market_time = self._get_val("/html/body/div[2]/header/div[4]/div[2]/div[2]/div/span")

        # لیست ارزها با استفاده از شناسه سطر و ستون اول (طبق تایید شما td[1])
        currencies = [
            ("☸️ دلار آمريکا", "//tr[@data-market-row='price_dollar_rl']/td[1]"),
            ("☸️ یورو", "//tr[@data-market-row='price_eur']/td[1]"),
            ("☸️ درهم آمارات", "//tr[@data-market-row='price_aed']/td[1]"),
            ("☸️ پوند انگلیس", "//tr[@data-market-row='price_gbp']/td[1]"),
            ("☸️ لیر ترکیه", "//tr[@data-market-row='price_try']/td[1]"),
            ("☸️ فرانک سوئیس", "//tr[@data-market-row='price_chf']/td[1]"),
            ("☸️ یوان چین", "//tr[@data-market-row='price_cny']/td[1]"),
            ("☸️ ین ژاپن", "//tr[@data-market-row='price_jpy']/td[1]"),
            ("☸️ وون کره جنوبی", "//tr[@data-market-row='price_krw']/td[1]"),
            ("☸️ دلار کانادا", "//tr[@data-market-row='price_cad']/td[1]"),
            ("☸️ دلار استرالیا", "//tr[@data-market-row='price_aud']/td[1]"),
            ("☸️ دلار نیوزلند", "//tr[@data-market-row='price_nzd']/td[1]"),
        ]

        coins = [
            ("✴️ سکه امامی", "//tr[@data-market-row='sekee']/td[1]"),
            ("✴️ سکه بهار آزادی", "//tr[@data-market-row='bahar']/td[1]"),
            ("✴️ نیم سکه", "//tr[@data-market-row='nim']/td[1]"),
            ("✴️ ربع سکه", "//tr[@data-market-row='rob']/td[1]"),
            ("✴️ سکه گرمی", "//tr[@data-market-row='gerami']/td[1]"),
        ]

        golds = [
            ("✴️ انس طلا", "//tr[@data-market-row='ons']/td[1]", "دلار"),
            ("✴️ طلای 18 عیار", "//tr[@data-market-row='geram18']/td[1]", "ریال"),
            ("✴️ طلای 24 عیار", "//tr[@data-market-row='geram24']/td[1]", "ریال"),
            ("✴️ طلای دست دوم", "//tr[@data-market-row='gold_mini_2']/td[1]", "ریال"),
        ]

        tether_val = self._get_val("//tr[@data-market-row='crypto-tether']/td[1]")
        bitcoin_val = self._get_val("//tr[@data-market-row='crypto-bitcoin']/td[1]")

        lines = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین", ""]

        for label, xpath in currencies:
            lines.append(f"{label}: {self._get_val(xpath)} ریال")

        for label, xpath in coins:
            lines.append(f"{label}: {self._get_val(xpath)} ریال")

        for label, xpath, unit in golds:
            lines.append(f"{label}: {self._get_val(xpath)} {unit}")

        lines.append(f"✴️ تتر: {tether_val} ریال")
        lines.append(f"✴️ بیت کوین: {bitcoin_val} دلار")
        lines.append("")
        lines.append(market_time)
        lines.append("ID: @aghayebazar_official")

        return "\n".join(lines)

    def run(self) -> Optional[str]:
        try:
            logger.info(f"Opening {self.TARGET_URL}...")
            self.driver.get(self.TARGET_URL)
            
            # بسیار مهم: صبر برای اجرای اسکریپت‌های قیمت‌گذاری سایت
            logger.info("Waiting 8 seconds for prices to update...")
            time.sleep(8) 
            
            report = self.build_report()
            
            with open(self.FILE_PATH, "w", encoding="utf-8") as f:
                f.write(report)
            
            logger.info("Market report saved to market_log.txt")
            return report
        except Exception as e:
            logger.error(f"Scraper error: {e}")
            return None

if __name__ == "__main__":
    browser = __webdriver__()
    try:
        scraper = TGJUScraper(browser)
        print(scraper.run())
    finally:
        browser.quit()
