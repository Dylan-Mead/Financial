"""Update per-ticker S&P 500 bar tables from Alpaca."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from time import sleep

import pandas as pd
import requests
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from db.pgsql import pgsql

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TICKERS_FILE = PROJECT_ROOT / "documentation" / "alpaca_tickers.txt"
SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
WIKIPEDIA_HEADERS = {
    "User-Agent": "FinancialTickerUpdater/1.0 (contact: your-email@example.com)"
}
INITIAL_START = datetime(1990, 1, 1, tzinfo=timezone.utc)
TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]*$")


def load_saved_tickers(path: Path = TICKERS_FILE) -> list[str]:
    """Read the previously processed ticker list."""
    if not path.exists():
        return []
    return [line.strip().upper() for line in path.read_text().splitlines() if line.strip()]


def load_sp500_tickers() -> list[str]:
    """Fetch the current S&P 500 ticker list from Wikipedia."""
    response = requests.get(SP500_URL, headers=WIKIPEDIA_HEADERS, timeout=30)
    response.raise_for_status()
    tables = pd.read_html(StringIO(response.text))
    if not tables or "Symbol" not in tables[0].columns:
        raise RuntimeError("Wikipedia response did not contain the S&P 500 Symbol column")

    tickers = (
        tables[0]["Symbol"]
        .astype(str)
        .str.strip()
        .str.upper()
        .tolist()
    )
    if not tickers:
        raise RuntimeError("Wikipedia returned an empty S&P 500 ticker list")
    invalid_tickers = [ticker for ticker in tickers if not TICKER_PATTERN.fullmatch(ticker)]
    if invalid_tickers:
        raise RuntimeError(f"Wikipedia returned invalid ticker symbols: {invalid_tickers}")
    return list(dict.fromkeys(tickers))


def append_tickers(tickers: list[str], path: Path = TICKERS_FILE) -> None:
    """Record newly processed tickers without duplicating existing entries."""
    if not tickers:
        return
    with path.open("a") as file:
        for ticker in tickers:
            file.write(f"{ticker}\n")


def normalize_timestamp(value: object) -> pd.Timestamp:
    """Return a UTC-aware pandas timestamp for a database or API value."""
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def bars_to_dataframe(bars: object, ticker: str) -> pd.DataFrame:
    """Convert an Alpaca bar response to the table shape used by this project."""
    dataframe = bars.df
    if dataframe.empty:
        return pd.DataFrame(
            {"timestamp": pd.Series(dtype="datetime64[ns, UTC]")}
        )
    dataframe = dataframe.reset_index()
    if "symbol" in dataframe.columns:
        dataframe = dataframe.drop(columns=["symbol"])
    if "timestamp" not in dataframe.columns:
        raise RuntimeError(f"Alpaca returned no timestamp column for {ticker}")
    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"], utc=True)
    return dataframe


def fetch_bars(
    client: StockHistoricalDataClient,
    ticker: str,
    start: datetime,
    end: datetime,
) -> pd.DataFrame:
    request = StockBarsRequest(
        symbol_or_symbols=ticker,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        feed=DataFeed.IEX,
    )
    try:
        return bars_to_dataframe(client.get_stock_bars(request), ticker)
    except Exception as error:
        raise RuntimeError(f"Failed to fetch bars for {ticker}: {error}") from error

def write_bars(db: pgsql, ticker: str, dataframe: pd.DataFrame) -> None:
    if dataframe.empty:
        return
    db.set_table_name(ticker.lower())
    db.set_pdf(dataframe)
    if not db.write_pdf_to_sql(if_exists="append"):
        raise RuntimeError(f"Failed to write bars for {ticker}")


def update_ticker(
    client: StockHistoricalDataClient,
    db: pgsql,
    connection: Connection,
    ticker: str,
    today: datetime,
) -> None:
    if len(ticker) == 0:
        return
    table_name = ticker.lower()
    table_exists = inspect(db.get_engine()).has_table(table_name)

    if not table_exists:
        dataframe = fetch_bars(client, ticker, INITIAL_START, today)
        write_bars(db, ticker, dataframe)
        print(f"{ticker}: created table with {len(dataframe)} rows")
        return

    max_date = connection.execute(
        text(f'SELECT MAX(timestamp) FROM "{table_name}"')
    ).scalar()
    if max_date is None:
        dataframe = fetch_bars(client, ticker, INITIAL_START, today)
    else:
        max_timestamp = normalize_timestamp(max_date)
        start = (max_timestamp + pd.Timedelta(days=1)).to_pydatetime()
        if start >= today:
            print(f"{ticker}: already current through {max_timestamp}")
            return
        dataframe = fetch_bars(client, ticker, start, today)
        dataframe = dataframe[dataframe["timestamp"] > max_timestamp]
    sleep(1)
    write_bars(db, ticker, dataframe)
    print(f"{ticker}: appended {len(dataframe)} rows")


def update_sp500_tables() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    saved_tickers = set(load_saved_tickers())
    try:
        sp500_tickers = load_sp500_tickers()
    except Exception as error:
        print(f"Warning: failed to refresh S&P 500 ticker list from Wikipedia ({error}); "
              "skipping the S&P 500 addition check for this run")
        sp500_tickers = []

    # Wikipedia is only used to discover brand-new S&P 500 tickers. Tickers
    # that drop off the official list (or are added manually) stay in
    # TICKERS_FILE and keep getting updated below.
    added_tickers = set(sp500_tickers) - saved_tickers
    if added_tickers:
        print(f"S&P 500 additions: {sorted(added_tickers)}")

    all_tickers = sorted(saved_tickers | added_tickers)

    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError(
            "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in "
            f"{PROJECT_ROOT / '.env'} or the environment."
        )

    db = pgsql()
    client = StockHistoricalDataClient(api_key, secret_key)
    today = datetime.now(timezone.utc)

    with db.get_engine().begin() as connection:
        for ticker in all_tickers:
#            print(ticker)
            try:
                update_ticker(client, db, connection, ticker, today)
                #sleep(1)
            except Exception as error:
                raise RuntimeError(f"Failed while updating {ticker}") from error

    append_tickers(sorted(added_tickers))


if __name__ == "__main__":
    update_sp500_tables()
