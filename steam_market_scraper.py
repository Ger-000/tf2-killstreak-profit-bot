import requests
from bs4 import BeautifulSoup
import time
from typing import Optional, Dict, List
import json

class SteamMarketScraper:
    """Scrapes Steam Community Market for TF2 item prices."""
    
    BASE_URL = "https://steamcommunity.com/market/search"
    ITEM_URL = "https://steamcommunity.com/market/listings/440/"
    
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
        """Search for an item on Steam Market."""
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
            
            # Find the first market listing
            listing = soup.find('a', class_='market_listing_row_link')
            
            if listing:
                item_name = listing.get('href', '').split('/listings/440/')[-1]
                return {'item_name': item_name, 'url': listing.get('href', '')}
            
            return None
            
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            return None
    
    def get_item_price(self, item_name: str) -> Optional[Dict]:
        """Get the current price of an item from Steam Market."""
        self._wait_for_rate_limit()
        
        try:
            url = f"{self.ITEM_URL}{item_name}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse JSON response from Steam Market
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Look for price data in the page
            price_text = soup.find('span', class_='market_price_summary')
            
            if price_text:
                # Extract price from text like "$0.03 USD"
                import re
                price_match = re.search(r'\$?([\d.]+)', price_text.get_text())
                if price_match:
                    price = float(price_match.group(1))
                    return {
                        'item_name': item_name,
                        'price': price,
                        'url': url
                    }
            
            return None
            
        except Exception as e:
            print(f"Error getting price for '{item_name}': {e}")
            return None
    
    def get_killstreak_kit_price(self, kit_name: str) -> Optional[Dict]:
        """Get price of a killstreak kit."""
        # Killstreak kits have specific naming convention
        search_name = f"{kit_name} Killstreak Kit"
        return self.get_item_price(search_name)
    
    def get_killstreak_weapon_price(self, weapon_name: str) -> Optional[Dict]:
        """Get price of a finished killstreak weapon."""
        search_name = f"{weapon_name} (Killstreak)"
        return self.get_item_price(search_name)
    
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