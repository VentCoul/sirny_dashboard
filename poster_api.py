import json
import requests
import os
import logging
from typing import List, Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'bot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PosterAPI")

class PosterAPI:
    """Class to interact with the Poster POS API."""
    
    def __init__(self, config_path: Optional[str] = None):
        if not config_path:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            self.token = self.config['access_token']
            self.account = self.config['account_name']
            self.base_url = f"https://{self.account}.joinposter.com/api"
            self.session = requests.Session()
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Internal method for requests with error handling."""
        url = f"{self.base_url}/{endpoint}"
        all_params = {"token": self.token}
        if params:
            all_params.update(params)
            
        try:
            response = self.session.get(url, params=all_params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # API often wraps data in 'response' key
            if isinstance(data, dict) and 'response' in data:
                return data['response']
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed ({endpoint}): {e}")
            return None

    def get_inventory_leftovers(self) -> List[Dict[str, Any]]:
        """Fetches storage leftovers from Poster."""
        data = self._make_request('storage.getStorageLeftovers')
        if isinstance(data, list):
            return [
                {
                    "ingredient_id": int(item.get('ingredient_id', 0)),
                    "ingredient_name": item.get('ingredient_name', 'Unknown'),
                    "leftover": float(item.get('ingredient_left', 0)),
                    "unit": item.get('ingredient_unit', ''),
                    "min_limit": float(item.get('limit_value', 0))
                }
                for item in data
            ]
        return []

    def get_clients(self) -> List[Dict[str, Any]]:
        """Fetches client database."""
        data = self._make_request('clients.getClients')
        return data if isinstance(data, list) else []

    def get_transactions(self, date_from: str, date_to: Optional[str] = None, status: int = 2) -> List[Dict[str, Any]]:
        """Fetches transactions for a period (YYYYMMDD). Status: 0-open, 1-closed (or 2 depending on account), 3-deleted."""
        params = {"date_from": date_from, "status": status}
        if date_to:
            params["date_to"] = date_to
            
        data = self._make_request('dash.getTransactions', params)
        return data if isinstance(data, list) else []

    def get_analytics(self, date_from: str, date_to: Optional[str] = None, type: str = 'products') -> List[Dict[str, Any]]:
        """Fetches analytics data (e.g. products, categories)."""
        params = {"date_from": date_from, "type": type}
        if date_to:
            params["date_to"] = date_to
        data = self._make_request('dash.getAnalytics', params)
        return data if isinstance(data, list) else []
