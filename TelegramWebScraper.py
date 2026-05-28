import time
import os
from pathlib import Path
from typing import Final
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
import num2words

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"

# =============================================================================
# Filesystem Path Resolution
# =============================================================================
# Using Path.cwd() (Current Working Directory) ensures the script remains 
# environment-agnostic. This resolves paths dynamically whether on Windows, 
# Linux, or cloud-synchronized environments like Proton Drive.

BASE_DIR: Final[Path] = Path(__file__).parent

CHROMEDRIVER_EXECUTABLE_PATH: Final[Path] = BASE_DIR / "chromedriver.exe"

class __webdriver__(webdriver.Chrome):
    def __init__(self, options=None, service=None, keep_alive=True):
        if service is None:
            try:
                service = ChromeService(executable_path=CHROMEDRIVER_EXECUTABLE_PATH, log_output=os.devnull)
            except TypeError:
                service = ChromeService(executable_path=CHROMEDRIVER_EXECUTABLE_PATH)
                try:
                    service.log_path = os.devnull
                except Exception:
                    pass

        if options is None:
            options = webdriver.ChromeOptions()
            options.add_argument("--incognito")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_experimental_option(
                "prefs", {"profile.default_content_setting_values.notifications": 2}
            )
            options.add_argument(f"--user-agent={USER_AGENT}")
            options.add_argument("--mute-audio")

            options.add_argument("--log-level=3")
            options.add_argument("--silent")
            options.add_argument("--disable-logging")
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-sync")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")

            options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            options.add_argument("--headless=new")
            options.add_argument("--window-size=2560,1440")
            options.add_argument("--force-device-scale-factor=1")
            options.add_argument("--high-dpi-support=1")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")

        super().__init__(options=options, service=service, keep_alive=keep_alive)

        self.set_window_size(2560, 1440)

    def find_element(self, by, value=None, timeout=5):
        start = time.time()
        last_exception = None
        while True:
            try:
                element = super().find_element(by, value)
                try:
                    self.execute_script(
                        "arguments[0].scrollIntoView({block:'center', inline:'center'});",
                        element
                    )
                except Exception:
                    pass
                return element
            except Exception as e:
                last_exception = e
                if time.time() - start >= timeout:
                    raise last_exception
                time.sleep(0.05)

    def get(self, url: str, timeout=15):
        start = time.time()
        last_exception = None
        while True:
            try:
                super().get(url)
                end = time.time() + timeout
                while time.time() < end:
                    try:
                        if self.execute_script("return document.readyState") == "complete":
                            break
                    except Exception:
                        pass
                    time.sleep(0.05)
                return
            except Exception as e:
                last_exception = e
                if time.time() - start >= timeout:
                    raise last_exception
                time.sleep(0.1)

    def read_text(self, by, value=None, timeout=5):
        el = self.find_element(by, value, timeout=timeout)

        end = time.time() + timeout
        while time.time() < end:
            txt = self.execute_script(
                "return (arguments[0].innerText || arguments[0].textContent || '').trim();",
                el
            )
            if txt:
                return txt

            val = el.get_attribute("value")
            if val and val.strip():
                return val.strip()

            aria = el.get_attribute("aria-label")
            if aria and aria.strip():
                return aria.strip()

            pseudo = self.execute_script(
                "return (getComputedStyle(arguments[0],'::before').content || '').replace(/^\"|\"$/g,'');",
                el
            )
            if pseudo and pseudo != "none":
                return pseudo

            time.sleep(0.05)

        return ""
