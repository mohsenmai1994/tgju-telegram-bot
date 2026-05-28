import os
import time
from pathlib import Path
from typing import Final

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from num2words import num2words


BASE_DIR: Final[Path] = Path(__file__).parent


class __webdriver__(webdriver.Chrome):
    def __init__(self, service=None, options=None):
        if options is None:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=2560,1440")
            options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_argument("--log-level=3")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-extensions")

        if service is None:
            service = ChromeService(log_output=os.devnull)

        super().__init__(service=service, options=options)
        self.set_window_size(2560, 1440)

    def find_element(self, by=By.ID, value=None):
        while True:
            try:
                return super().find_element(by=by, value=value)
            except Exception:
                time.sleep(0.5)

    def get(self, url: str):
        while True:
            try:
                return super().get(url)
            except Exception:
                time.sleep(1)

    def read_text(self, by=By.TAG_NAME, value="body") -> str:
        while True:
            try:
                element = super().find_element(by=by, value=value)
                return element.text
            except Exception:
                time.sleep(0.5)
