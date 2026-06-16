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
            # تنظیمات بهینه برای GitHub Actions و جلوگیری از بلاک شدن
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument(f"--user-agent={USER_AGENT}")
            options.add_argument("--window-size=2560,1440")
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            # This is crucial to look like a real browser
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
            # Disable the "AutomationControlled" flag
            options.add_argument('--disable-blink-features=AutomationControlled')

        super().__init__(options=options, service=service, keep_alive=keep_alive)
        self.set_window_size(2560, 1440)

    # ... بقیه متدهای find_element و read_text بدون تغییر باقی بمانند ...
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
            # صبر برای لود کامل DOM
            time.sleep(2) 
        except Exception as e:
            print(f"Error loading page: {e}")
