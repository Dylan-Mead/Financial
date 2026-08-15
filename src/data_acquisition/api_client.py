"""Example API client for data acquisition.

Replace fetch_data implementation with your external API endpoints and parsing.
"""
import requests
from typing import List, Dict
from ..config import EXTERNAL_API_BASE

class APIClient:
    def __init__(self, base_url: str = EXTERNAL_API_BASE, session: requests.Session | None = None):
        self.base_url = base_url
        self.session = session or requests.Session()

    def fetch_data(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Fetch sample data for a symbol. Return list of dict rows.
        This is a stub — adapt to the real API's shape and auth.
        """
        url = f"{self.base_url}/data/{symbol}"
        params = {"limit": limit}
        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Expect data to be a list of records
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return data

if __name__ == "__main__":
    c = APIClient()
    print("Fetched (stub):", c.fetch_data("AAPL", limit=2))
