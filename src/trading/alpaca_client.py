"""Wrapper around Alpaca REST trading API.

Uses the alpaca-trade-api package. This wrapper keeps a small surface for placing orders
and checking account status. Use env vars for keys.
"""
from typing import Any
from alpaca_trade_api.rest import REST, TimeFrame
from ..config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL

class AlpacaClient:
    def __init__(self, api_key: str | None = None, secret_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or ALPACA_API_KEY
        self.secret_key = secret_key or ALPACA_SECRET_KEY
        self.base_url = base_url or ALPACA_BASE_URL
        if not all([self.api_key, self.secret_key, self.base_url]):
            raise RuntimeError("Alpaca credentials/base URL not configured in env")
        self.client = REST(self.api_key, self.secret_key, self.base_url)

    def get_account(self) -> Any:
        return self.client.get_account()

    def submit_order(self, symbol: str, qty: float, side: str = "buy", order_type: str = "market", time_in_force: str = "gtc") -> Any:
        """Place an order. side: 'buy' or 'sell'"""
        return self.client.submit_order(symbol=symbol, qty=qty, side=side, type=order_type, time_in_force=time_in_force)

    def get_bars(self, symbol: str, timeframe: str = "1D", limit: int = 100):
        tf = TimeFrame.Day if timeframe == "1D" else TimeFrame.Minute
        return self.client.get_bars(symbol, tf, limit=limit).df

if __name__ == "__main__":
    # Example quick check (paper account recommended)
    try:
        a = AlpacaClient()
        acc = a.get_account()
        print("Account status:", acc.status)
    except Exception as e:
        print("Alpaca client error (expected in skeleton):", e)
