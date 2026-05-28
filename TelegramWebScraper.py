from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final, List, Optional, Dict

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from Scraper import __webdriver__

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("TGJU_FULL_XPATH")

class TGJUScraper:
    TARGET_URL: Final[str] = "https://www.tgju.org/"
    BASE_DIR: Final[Path] = Path(__file__).parent
    FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"

    # XPaths اصلی
    XPATHS = {
        "ONS": '/html/body/main/div[4]/div[3]/div[1]/table/tbody/tr',
        "GOLD": '/html/body/main/div[4]/div[3]/div[2]/table/tbody/tr',
        "MESGHAL": '/html/body/main/div[4]/div[4]/div[1]/table/tbody/tr',
        "COIN": '/html/body/main/div[4]/div[4]/div[10]/table/tbody/tr',
        "CURRENCY_1": '/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[1]/table/tbody/tr',
        "CURRENCY_2": '/html/body/main/div[4]/div[8]/div[2]/div/div[1]/div[2]/div/div[2]/table/tbody/tr',
        "INFO": '/html/body/main/div[1]/div[2]/div/ul/li'
    }

    # ردیف‌های مورد نیاز از هر جدول بر اساس کد شما
    TABLE_CONFIG = {
        "GOLD": [1, 2], # طلای 18 و 24
        "COIN": [1, 2, 3, 4], # امامی، بهار، نیم، ربع
        "CURRENCY_1": [1, 2, 10], # دلار، یورو، درهم (نمونه)
        "INFO": [1, 2, 4, 5, 6] # شاخص‌های بالای صفحه
    }

    def __init__(self, driver) -> None:
        self.driver = driver
        self.results = []

    def get_text_safe(self, xpath: str) -> str:
        """خواندن متن با مدیریت خطا"""
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            return element.text.strip()
        except:
            return "N/A"

    def extract_table_data(self, xpath_base: str, rows: List[int], section_name: str):
        """استخراج داده از ردیف‌های مشخص شده یک جدول"""
        logger.info(f"Processing section: {section_name}")
        for row_index in rows:
            try:
                name_xpath = f"{xpath_base}[{row_index}]/th"
                price_xpath = f"{xpath_base}[{row_index}]/td[1]"
                change_xpath = f"{xpath_base}[{row_index}]/td[2]"

                name = self.get_text_safe(name_xpath)
                price = self.get_text_safe(price_xpath)
                change = self.get_text_safe(change_xpath)

                if name != "N/A":
                    self.results.append(f"🔹 {name}: {price} ({change})")
            except Exception as e:
                logger.warning(f"Error in {section_name} row {row_index}: {e}")

    def extract_info_bar(self):
        """استخراج اطلاعات نوار بالای سایت"""
        for i in self.TABLE_CONFIG["INFO"]:
            name = self.get_text_safe(f"{self.XPATHS['INFO']}[{i}]/h3")
            price = self.get_text_safe(f"{self.XPATHS['INFO']}[{i}]/span[1]")
            if name != "N/A":
                self.results.append(f"🔸 {name}: {price}")

    def build_report(self) -> str:
        """تجمیع تمام بخش‌ها در یک متن"""
        report_lines = ["📊 **گزارش لحظه‌ای بازار**", ""]
        
        # ۱. اطلاعات شاخص‌های اصلی (بالای صفحه)
        self.extract_info_bar()
        report_lines.extend(self.results)
        self.results = [] # خالی کردن برای بخش بعدی

        report_lines.append("\n💰 **ارز و مسکوکات**")
        
        # ۲. استخراج جداول مختلف
        self.extract_table_data(self.XPATHS["CURRENCY_1"], self.TABLE_CONFIG["CURRENCY_1"], "Currencies")
        self.extract_table_data(self.XPATHS["GOLD"], self.TABLE_CONFIG["GOLD"], "Gold")
        self.extract_table_data(self.XPATHS["COIN"], self.TABLE_CONFIG["COIN"], "Coins")
        
        report_lines.extend(self.results)
        
        report_lines.append("\n🆔 @aghayebazar_official")
        return "\n".join(report_lines)

    def run(self) -> Optional[str]:
        try:
            logger.info(f"Navigating to {self.TARGET_URL}")
            self.driver.get(self.TARGET_URL)
            
            # منتظر ماندن برای لود شدن جدول (حداکثر ۱۰ ثانیه)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_id_located((By.ID, "footer"))
            )

            report = self.build_report()

            # ذخیره در فایل برای اطمینان
            self.FILE_PATH.write_text(report, encoding="utf-8")
            logger.info("Report generated successfully.")
            return report
        except Exception as exc:
            logger.error(f"Pipeline failed: {exc}")
            return None

if __name__ == "__main__":
    browser = __webdriver__()
    try:
        scraper = TGJUScraper(browser)
        print(scraper.run())
    finally:
        browser.quit()
