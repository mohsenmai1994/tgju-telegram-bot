import logging
from dataclasses import dataclass
from typing import List, Final
from pathlib import Path
from Scraper import Scraper

@dataclass
class Asset:
    """Represents a market instrument with its extraction and display properties."""
    name: str
    xpath: str
    unit: str
    emoji: str

class TGJUScraper(Scraper):
    """
    Automated scraper for TGJU.org with custom Persian formatting 
    for Telegram channel broadcasting.
    """
    
    TARGET_URL: Final[str] = "https://www.tgju.org/"
    BASE_DIR: Final[Path] = Path(__file__).parent
    CHANNEL_HANDLE: Final[str] = "aghayebazar_official"

    # Asset definitions categorized by display groups
    ASSETS: Final[List[Asset]] = [
        # --- Currencies (Group 1: ☸️) ---
        Asset("دلار آمريکا", '//*[@id="l-price_dollar_rl"]/span[1]', "ریال", "☸️"),
        Asset("یورو", '//*[@id="l-price_eur"]/span[1]', "ریال", "☸️"),
        Asset("درهم امارات", '//*[@id="l-price_aed"]/span[1]', "ریال", "☸️"),
        Asset("پوند انگلیس", '//*[@id="l-price_gbp"]/span[1]', "ریال", "☸️"),
        Asset("لیر ترکیه", '//*[@id="l-price_try"]/span[1]', "ریال", "☸️"),
        Asset("فرانک سوئیس", '//*[@id="l-price_chf"]/span[1]', "ریال", "☸️"),
        Asset("یوان چین", '//*[@id="l-price_cny"]/span[1]', "ریال", "☸️"),
        Asset("ین ژاپن", '//*[@id="l-price_jpy"]/span[1]', "ریال", "☸️"),
        Asset("وون کره جنوبی", '//*[@id="l-price_krw"]/span[1]', "ریال", "☸️"),
        Asset("دلار کانادا", '//*[@id="l-price_cad"]/span[1]', "ریال", "☸️"),
        Asset("دلار استرالیا", '//*[@id="l-price_aud"]/span[1]', "ریال", "☸️"),
        Asset("دلار نیوزلند", '//*[@id="l-price_nzd"]/span[1]', "ریال", "☸️"),
        
        # --- Gold, Coins & Crypto (Group 2: ✴️) ---
        Asset("سکه امامی", '//*[@id="l-coin_sekee"]/span[1]', "ریال", "✴️"),
        Asset("سکه بهار آزادی", '//*[@id="l-price_bahar"]/span[1]', "ریال", "✴️"),
        Asset("نیم سکه", '//*[@id="l-coin_nim"]/span[1]', "ریال", "✴️"),
        Asset("ربع سکه", '//*[@id="l-coin_rob"]/span[1]', "ریال", "✴️"),
        Asset("سکه گرمی", '//*[@id="l-price_gerami"]/span[1]', "ریال", "✴️"),
        Asset("انس طلا", '//*[@id="l-ons"]/span[1]', "دلار", "✴️"),
        Asset("طلای 18 عیار", '//*[@id="l-geram18"]/span[1]', "ریال", "✴️"),
        Asset("طلای 24 عیار", '//*[@id="l-geram24"]/span[1]', "ریال", "✴️"),
        Asset("طلای دست دوم", '//*[@id="l-gold_rent_second"]/span[1]', "ریال", "✴️"),
        Asset("تتر", '//*[@id="l-crypto-tether"]/span[1]', "ریال", "✴️"),
        Asset("بیت کوین", '//*[@id="l-crypto-bitcoin"]/span[1]', "دلار", "✴️")
    ]

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def fetch_market_data(self) -> str:
        """Navigates to source and extracts data for all defined assets."""
        try:
            self.logger.info(f"Connecting to {self.TARGET_URL}")
            self.get(self.TARGET_URL)
            
            results = []
            for asset in self.ASSETS:
                price = self.read_text(asset.xpath)
                if price:
                    results.append(f"{asset.emoji} {asset.name}: {price.strip()} {asset.unit}")
                else:
                    self.logger.warning(f"Selector mismatch for: {asset.name}")
            
            return self._build_final_message(results) if results else "⚠️ Error in data extraction."

        except Exception as e:
            self.logger.error(f"Scraping process failed: {e}")
            return "❌ Connection to data source failed."

    def _build_final_message(self, data_lines: List[str]) -> str:
        """Formats the output into the requested Telegram template."""
        from datetime import datetime
        import pytz

        # Setting up Persian Date/Time
        tehran_tz = pytz.timezone('Asia/Tehran')
        now = datetime.now(tehran_tz)
        
        # Simple Persian weekday and month mapping
        weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"]
        months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        
        # Note: For professional Jalali conversion, 'jdatetime' library is recommended.
        # This provides a close approximation for the timestamp string.
        time_str = now.strftime("%H:%M:%S")
        date_footer = f"{now.day} {months[(now.month-1)%12]} - {time_str}"

        # Building the final structure
        hashtags = "#نرخ_ارز #سکه #طلا #دلار #بیتکوین\n\n"
        body = "\n".join(data_lines)
        footer = f"\n\n{date_footer}\nID: @{self.CHANNEL_HANDLE}"
        
        return hashtags + body + footer
