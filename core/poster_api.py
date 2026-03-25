import requests
import json
import os
import logging

logger = logging.getLogger("PosterAPI")

class PosterAPI:
    def __init__(self):
        self.config = self._load_config()
        self.base_url = f"https://{self.config.get('account_name')}.joinposter.com/api"
        self.token = self.config.get('access_token')

    def _load_config(self):
        # Try multiple paths for config.json
        base_dir = os.path.dirname(os.path.abspath(__file__))
        paths_to_try = [
            os.path.join(base_dir, 'config.json'),
            os.path.join(os.path.dirname(base_dir), 'config.json'),
            os.path.join(os.path.dirname(base_dir), 'data', 'config.json')
        ]
        for path in paths_to_try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        raise FileNotFoundError("Config file not found in any expected location.")

    def _make_request(self, method, params=None):
        if params is None: params = {}
        params['token'] = self.token
        try:
            response = requests.get(f"{self.base_url}/{method}", params=params)
            return response.json().get('response', [])
        except Exception as e:
            logger.error(f"API Error ({method}): {e}")
            return []

    def get_transactions(self, date_from, date_to, status=2):
        return self._make_request('dash.getTransactions', {
            'date_from': date_from,
            'date_to': date_to,
            'status': status
        })
