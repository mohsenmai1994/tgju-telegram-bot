import time
import os
import platform
from pathlib import Path
from typing import Final
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

BASE_DIR: Final[Path] = Path(__file__).parent

class __webdriver__(webdriver.Chrome):
    def __init__(self, options=None, service=None, keep_alive=True):
        if options is None:
            options = webdriver.ChromeOptions()
            
            # ۱. تنظیمات پایه‌ای اجرا در حالت بدون گرافیک (Headless)
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            
            # ۲. غیرفعال کردن لود تصاویر و استایل‌ها برای افزایش چشمگیر سرعت لود صفحات
            options.add_argument("--blink-settings=imagesEnabled=false")
            
            # ۳. غیرفعال کردن اکستنشن‌ها، ابزارهای اضافه و نوتیفیکیشن‌ها برای صرفه‌جویی در منابع
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-impl-side-painting")
            options.add_argument("--disable-setuid-sandbox")
            options.add_argument("--disable-web-security")
            
            # ۴. هویت و ابعاد پنجره (شبیه‌سازی مرورگر واقعی)
            options.add_argument(f"--user-agent={USER_AGENT}")
            options.add_argument("--window-size=2560,1440")
            
            # ۵. غیرفعال کردن شناسایی به عنوان ربات و خاموش کردن لاگ‌های سیستمی کروم
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--dns-prefetch-disable')

        super().__init__(options=options, service=service, keep_alive=keep_alive)
        self.set_window_size(2560, 1440)

    def find_element(self, by, value=None, timeout=5):
        start = time.time()
        last_exception = None
        while True:
            try:
                element = super().find_element(by, value)
                return element
            except Exception as e:
                last_exception = e
                if time.time() - start >= timeout:
                    raise last_exception
                time.sleep(0.05)

    def get(self, url: str, timeout=15):
        try:
            super().get(url)
            # صبر برای لود کامل DOM (در صورت نیاز می‌توانید به ۰.۵ یا ۱ ثانیه کاهش دهید تا سریع‌تر شود)
            time.sleep(1) 
        except Exception as e:
            print(f"Error loading page: {e}")
