import requests
from bs4 import BeautifulSoup
import time
from typing import Optional, Dict, List
import json
from urllib.parse import unquote, quote
import re

class SteamMarketScraper:
    """Scrapes Steam Community Market for TF2 item prices."""
    
    BASE_URL = "https://steamcommunity.com/market/search"
    ITEM_URL = "https://steamcommunity.com/market/listings/440/"
    PRICE_OVERVIEW = "https://steamcommunity.com/market/priceoverview/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.rate_limit = 2  # seconds between requests
        self.last_request = 0
    
    def _wait_for_rate_limit(self):
        """Respects rate limiting to avoid getting blocked."""
        elapsed = time.time() - self.last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request = time.time()
    
    def search_item(self, query: str) -> Optional[Dict]:
        """Search for an item on Steam Market and return its canonical market_hash_name and URL.

        Returns {'market_hash_name': <str>, 'url': <str>} or None if not found.
        """
        self._wait_for_rate_limit()
        params = {
            'q': query,
            'category_440': '0',
            'appid': '440'
        }
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            listing = soup.find('a', class_='market_listing_row_link')
            if listing and listing.get('href'):
                href = listing.get('href')
                # href example: /market/listings/440/Minigun%20(Killstreak)
                market_hash = href.split('/listings/440/')[-1]
                # decode percent-encoding to get canonical name
                market_hash_decoded = unquote(market_hash)
                url = f"https://steamcommunity.com{href}"
                return {'market_hash_name': market_hash_decoded, 'url': url}
            return None
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            return None
    
    def _parse_price_string(self, price_str: str) -> Optional[float]:
        """Parse a price string from Steam like '€0,03', '$0.03' or '0,03 €' into a float.

        Returns float price or None on failure.
        """
        if not price_str:
            return None
        # Try to extract the numeric portion
        m = re.search(r"[\d\.,]+", price_str)
        if not m:
            return None
        num = m.group(0)
        # If there are both '.' and ',', assume '.' is decimal and ',' thousand sep -> remove commas
        if '.' in num and ',' in num:
            num = num.replace(',', '')
        # If only comma present, treat it as decimal separator
        elif ',' in num and '.' not in num:
            num = num.replace(',', '.')
        try:
            return float(num)
        except ValueError:
            return None
    
    def get_item_price(self, item_name: str) -> Optional[Dict]:
        """Get the current price of an item from Steam Market using the priceoverview API.

        item_name can be a user-provided name (e.g. 'Minigun (Killstreak)') or a canonical
        market_hash_name. This method will try to find the canonical name via search if needed.
        """
        self._wait_for_rate_limit()
        try:
            # If the item_name looks like a URL-encoded slug (contains %), decode it
            market_hash_name = item_name
            # If it looks like a human name (spaces) we'll try to search for the canonical name first
            if ' ' in item_name or '%' in item_name or '(' in item_name or ')' in item_name:
                search = self.search_item(item_name)
                if search:
                    market_hash_name = search['market_hash_name']
                else:
                    # fallback to using the raw item_name as market_hash_name
                    market_hash_name = item_name
            # Query the priceoverview endpoint
            params = {
                'country': 'DE',        # country doesn't affect numbers, but keeps formatting consistent
                'currency': '3',        # 3 is EUR in Steam's API
                'appid': '440',
                'market_hash_name': market_hash_name
            }
            response = self.session.get(self.PRICE_OVERVIEW, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data or not data.get('success'):
                # Price overview not available
                return None
            # 'lowest_price' or 'median_price' may be present
            price_field = data.get('lowest_price') or data.get('median_price')
            if not price_field:
                return None
            price = self._parse_price_string(price_field)
            if price is None:
                return None
            # Build a canonical URL to the listing
            listing_url = f"{self.ITEM_URL}{quote(market_hash_name)}"
            return {
                'item_name': market_hash_name,
                'price': price,
                'url': listing_url
            }
        except Exception as e:
            print(f"Error getting price for '{item_name}': {e}")
            return None
    
    def get_killstreak_kit_price(self, kit_name: str) -> Optional[Dict]:
        """Get price of a killstreak kit by searching for the canonical kit listing."""
        search_name = f"{kit_name} Killstreak Kit"
        search = self.search_item(search_name)
        if not search:
            return None
        return self.get_item_price(search['market_hash_name'])
    
    def get_killstreak_weapon_price(self, weapon_name: str) -> Optional[Dict]:
        """Get price of a finished killstreak weapon by searching for the canonical listing."""
        search_name = f"{weapon_name} (Killstreak)"
        search = self.search_item(search_name)
        if not search:
            return None
        return self.get_item_price(search['market_hash_name'])
    
    def calculate_profit(self, kit_price: float, weapon_price: float, base_weapon_cost: float = 0.0017) -> Dict:
        """
        Calculate profit margin considering Steam's 13% tax.
        
        Args:
            kit_price: Price of the killstreak kit
            weapon_price: Current market price of finished killstreak weapon
            base_weapon_cost: Cost of base weapon (default 0.0017€)
        
        Returns:
            Dict with profit analysis
        """
        
        STEAM_TAX = 0.13
        
        # Total cost to create the weapon
        total_cost = kit_price + base_weapon_cost
        
        # If we sell at market price, after 13% tax
        revenue_at_market = weapon_price * (1 - STEAM_TAX)
        
        # Profit if selling at market price
        profit_at_market = revenue_at_market - total_cost
        
        # Calculate optimal resale price (market price minus small margin for quick sale)
        optimal_resale = weapon_price * 0.98  # 2% below market
        revenue_at_optimal = optimal_resale * (1 - STEAM_TAX)
        profit_at_optimal = revenue_at_optimal - total_cost
        
        profit_margin_percent = (profit_at_market / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'base_weapon_cost': base_weapon_cost,
            'kit_price': kit_price,
            'total_cost': total_cost,
            'market_price': weapon_price,
            'optimal_resale_price': optimal_resale,
            'profit_at_market': profit_at_market,
            'profit_at_optimal': profit_at_optimal,
            'profit_margin_percent': profit_margin_percent,
            'is_profitable': profit_at_optimal > 0
        }
