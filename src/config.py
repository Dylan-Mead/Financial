"""Basic configuration and env loading.

Uses python-dotenv in development; production should inject env variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # safe to call even when .env is absent

DATABASE_URL = os.getenv("DATABASE_URL")
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
EXTERNAL_API_BASE = os.getenv("EXTERNAL_API_BASE", "https://api.example.com")

# Simple helper to ensure required config
REQUIRED = ["DATABASE_URL"]
missing = [k for k in REQUIRED if not globals().get(k)]
if missing:
    # Do not raise here to keep skeleton import-safe; scripts should assert as needed
    pass
