"""Simple script to fetch data via APIClient and insert to Postgres.

Run as: python scripts/collect_data.py SYMBOL
"""
import sys
from datetime import datetime
from src.data_acquisition.api_client import APIClient
from src.db.pg import insert_rows, init_db, get_engine


def main(symbol: str):
    client = APIClient()
    rows = client.fetch_data(symbol, limit=100)
    # Expect rows as list of dicts that contain at least timestamp and price
    prepared = []
    for r in rows:
        # adapt keys to your API. This is a placeholder mapping
        prepared.append({
            "symbol": symbol,
            "ts": r.get("timestamp") or r.get("ts") or datetime.utcnow(),
            "price": r.get("price") or r.get("close") or None,
            "raw": str(r),
        })
    engine = get_engine()
    init_db(engine)
    insert_rows(prepared, engine)
    print(f"Inserted {len(prepared)} rows for {symbol}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/collect_data.py SYMBOL")
        sys.exit(1)
    main(sys.argv[1])
