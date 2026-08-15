"""Script to execute a simple trade via AlpacaClient.

Run as: python scripts/execute_trade.py BUY|SELL SYMBOL QTY
"""
import sys
from src.trading.alpaca_client import AlpacaClient


def main(action: str, symbol: str, qty: float):
    alp = AlpacaClient()
    side = "buy" if action.lower() in ("buy", "b") else "sell"
    order = alp.submit_order(symbol, qty, side=side)
    print("Submitted order:", order)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python scripts/execute_trade.py BUY|SELL SYMBOL QTY")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]))
