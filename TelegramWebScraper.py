from __future__ import annotations

import time
from pathlib import Path

from Scraper import __webdriver__
from selenium.webdriver.common.by import By


TARGET_URL = "https://www.tgju.org/"
BASE_DIR = Path(__file__).parent

BEFORE_PATH = BASE_DIR / "before_scroll.png"
AFTER_PATH = BASE_DIR / "after_scroll_currency.png"


def main() -> None:
    browser = __webdriver__()

    try:
        browser.get(TARGET_URL)
        time.sleep(6)

        browser.save_screenshot(str(BEFORE_PATH))
        print(f"Saved: {BEFORE_PATH}")

        currency_section_xpath = "/html/body/main/div[4]/div[8]"
        currency_section = browser.find_element(By.XPATH, currency_section_xpath)

        browser.execute_script(
            "arguments[0].scrollIntoView({behavior: 'instant', block: 'start'});",
            currency_section
        )
        time.sleep(2)

        browser.save_screenshot(str(AFTER_PATH))
        print(f"Saved: {AFTER_PATH}")

    finally:
        browser.quit()


if __name__ == "__main__":
    main()
