import pandas as pd
import json
import ollama
#from pydantic import BaseModel, Field
import json
from db.pgsql import pgsql
import ast

from datetime import datetime, timedelta, timezone
#from getpass import getpass
from pathlib import Path
import os
import time

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
ASSETS_US_EQUITY_FILE = PROJECT_ROOT / "tests" / "assets_us_equity.json"
MAX_REQUEST_ATTEMPTS = 4
INITIAL_RETRY_DELAY_SECONDS = 5
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}



def get_api_key_secret():
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise ValueError(
            "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in "
            f"{PROJECT_ROOT / '.env'} or the environment."
        )
    return api_key, secret_key

if __name__ == "__main__":
    api_key, secret_key = get_api_key_secret()
    print(f"API Key: {api_key[:4]}...{api_key[-4:]}")
    print(f"Secret Key: {secret_key[:4]}...{secret_key[-4:]}")