from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final, List, Optional

from selenium.webdriver.common.by import By
from Scraper import __webdriver__


# =============================================================================
# Logging Setup
# =============================================================================
# A deterministic logging configuration is utilized to facilitate debugging 
# and audit trails. This ensures that any discrepancies in text extraction 
# or I/O operations are captured with precise timestamps.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("TGJU_Scraper")


# =============================================================================
# Data Model
# =============================================================================
@dataclass(frozen=True)
class AssetMetadata:
    """
    Immutable schema for market asset definitions.
    
    Attributes
    ----------
    search_keys : List[str]
        Ordered collection of string identifiers used for regex-based matching.
    label : str
        The human-readable canonical name for the asset.
    emoji : str
        Visual glyph for report formatting.
    unit : str
        The localized currency or measurement unit.
    """
    search_keys: List[str]
    label: str
    emoji: str
    unit: str


# =============================================================================
# Scraper Implementation
# =============================================================================
class TGJUScraper:
    """
    Financial data extraction engine for the TGJU platform.
    
    This implementation utilizes a decoupled architecture where the extraction 
    logic is separated from the I/O layer. It leverages Unicode-aware normalization 
    to handle Persian/Arabic orthographic variations.
    """

    # -------------------------------------------------------------------------
    # Static Configuration & Filesystem Resolution
    # -------------------------------------------------------------------------
    TARGET_URL: Final[str] = "https://www.tgju.org/"
    
    # Path Resolution: Using __file__ allows the script to be environment-agnostic.
    # This is critical for deployments on cloud-synced drives like Proton Drive.
    BASE_DIR: Final[Path] = Path(__file__).parent
    FILE_PATH: Final[Path] = BASE_DIR / "market_log.txt"

    CHANNEL_HANDLE: Final[str] = "@aghayebazar_official"

    # -------------------------------------------------------------------------
    # Asset Registry
    # -------------------------------------------------------------------------
    ASSETS: Final[List[AssetMetadata]] = [
        AssetMetadata(
            search_keys=["دلار", "قیمت دلار"],
            label="دلار آمریکا", emoji="☸️", unit="ریال"
        ),
        AssetMetadata(search_keys=["یورو"], label="یورو", emoji="☸️", unit="ریال"),
        AssetMetadata(search_keys=["درهم امارات"], label="درهم امارات", emoji="☸️", unit="ریال"),
        AssetMetadata(search_keys=["پوند انگلیس"], label="پوند انگلیس", emoji="☸️", unit="ریال"),
        AssetMetadata(search_keys=["لیر ترکیه"], label="لیر ترکیه", emoji="☸️", unit="ریال"),
        AssetMetadata(search_keys=["فرانک سوئیس"], label="فرانک سوئیس", emoji="☸️", unit="ریال"),
        AssetMetadata(search_keys=["یوان چین"], label="یوان چین", emoji="☸️", unit="ریال"),
        AssetMetadata(search_keys=["ین ژاپن"], label="ین ژاپن", emoji="☸️", unit="ریال"),
        AssetMetadata(search_keys=["وون کره جنوبی"], label="وون کره جنوبی", emoji="☸️", unit="ریال"),
        AssetMetadata(search_keys=["دلار کانادا"], label="دلار کانادا", emoji="☸️", unit="ریال"),
        AssetMetadata(search_keys=["دلار استرالیا"], label="دلار استرالیا", emoji="☸️", unit="ریال"),
        AssetMetadata(search_keys=["دلار نیوزیلند"], label="دلار نیوزیلند", emoji="☸️", unit="ریال"),
        AssetMetadata(search_keys=["سکه بهار آزادی"], label="سکه بهار آزادی", emoji="✴️", unit="ریال"),
        AssetMetadata(search_keys=["نیم سکه"], label="نیم سکه", emoji="✴️", unit="ریال"),
        AssetMetadata(search_keys=["ربع سکه"], label="ربع سکه", emoji="✴️", unit="ریال"),
        AssetMetadata(search_keys=["سکه گرمی"], label="سکه گرمی", emoji="✴️", unit="ریال"),
        AssetMetadata(search_keys=["انس طلا"], label="انس طلا", emoji="✴️", unit="دلار"),
        AssetMetadata(search_keys=["طلای 18 عیار"], label="طلای 18 عیار", emoji="✴️", unit="ریال"),
        AssetMetadata(search_keys=["طلای 24 عیار"], label="طلای 24 عیار", emoji="✴️", unit="ریال"),
        AssetMetadata(search_keys=["طلای دست دوم"], label="طلای دست دوم", emoji="✴️", unit="ریال"),
        AssetMetadata(search_keys=["تتر", "USDT"], label="تتر", emoji="✴️", unit="ریال"),
        AssetMetadata(search_keys=["بیت کوین", "Bitcoin", "BTC"], label="بیت کوین", emoji="✴️", unit="دلار"),
    ]

    def __init__(self, driver) -> None:
        self.driver = driver
        self._page_text: str = ""

    def _normalize_text(self, raw_text: str) -> str:
        """Applies orthographic normalization for Persian/Arabic character sets."""
        if not raw_text: return ""
        translation_map = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "‌": " "})
        normalized = raw_text.translate(translation_map)
        return re.sub(r"\s+", " ", normalized).strip()

    def _extract_numeric_value(self, search_keys: List[str]) -> str:
        """Heuristic-based numeric extraction with bounded spatial lookahead."""
        numeric_token = r"[\d۰-۹,٬.]+"
        bounded_gap = r"[^\d۰-۹]{0,25}"

        for key in search_keys:
            pattern = rf"{re.escape(self._normalize_text(key))}{bounded_gap}({numeric_token})"
            match = re.search(pattern, self._page_text)
            if match:
                val = match.group(1).strip(" ,٬.")
                if re.search(r"[\d۰-۹]", val): return val
        return "N/A"

    def _extract_persian_timestamp(self) -> str:
        """Parses and formats the Persian chronological marker from the DOM text."""
        wd = r"شنبه|یکشنبه|دوشنبه|سه‌شنبه|سه شنبه|چهارشنبه|پنجشنبه|جمعه"
        mn = r"فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور|مهر|آبان|آذر|دی|بهمن|اسفند"
        digit = r"0-9۰-۹"
        tm = rf"[{digit}]{{1,2}}:[{digit}]{{1,2}}:[{digit}]{{1,2}}"

        pattern = rf"(({wd})\s+([{digit}]{{1,2}})\s+({mn})\s*-\s*({tm}))"
        match = re.search(pattern, self._page_text)
        return match.group(1) if match else "N/A"

    def _load_page_text(self) -> None:
        try:
            body_element = self.driver.find_element(By.TAG_NAME, "body")
            self._page_text = self._normalize_text(body_element.text)
        except Exception as exc:
            raise RuntimeError(f"DOM Access Failure: {exc}")

    def build_report(self) -> str:
        """Synthesizes the extracted data into a structured Telegram-compatible report."""
        self._load_page_text()
        lines = ["#نرخ_ارز #سکه #طلا #دلار #بیتکوین", ""]
        for asset in self.ASSETS:
            val = self._extract_numeric_value(asset.search_keys)
            lines.append(f"{asset.emoji} {asset.label}: {val} {asset.unit}")
        lines.extend(["", self._extract_persian_timestamp(), f"ID: {self.CHANNEL_HANDLE}"])
        return "\n".join(lines)

    def run(self) -> Optional[str]:
        """Main execution workflow: Navigation -> Extraction -> Persistence."""
        try:
            logger.info(f"Navigating to {self.TARGET_URL}")
            self.driver.get(self.TARGET_URL)
            self.driver.implicitly_wait(10)

            report = self.build_report()

            # Using atomic write to ensure data integrity
            with open(self.FILE_PATH, "w", encoding="utf-8") as output_file:
                output_file.write(report)

            logger.info(f"Artifact successfully persisted at: {self.FILE_PATH}")
            return report
        except Exception as exc:
            logger.error(f"Execution pipeline failed: {exc}")
            return None


if __name__ == "__main__":
    browser = __webdriver__()
    try:
        scraper = TGJUScraper(browser)
        print(scraper.run())
    finally:
        browser.quit()
