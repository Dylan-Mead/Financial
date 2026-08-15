Financial project skeleton

Structure:
- src/
  - config.py               # load env / config
  - data_acquisition/       # API client(s) to fetch external data
  - db/                     # Postgres read/write helpers (SQLAlchemy)
  - trading/                # Alpaca trading wrapper
  - visualization/          # local plotting utilities
- web/                      # Flask app + static assets
- scripts/                  # small CLI scripts to run data collection & trades

Setup (quick):
1. Python 3.10+
2. pip install -r requirements.txt
3. Copy .env.example -> .env and set values
4. Run scripts/collect_data.py to fetch and store sample data
5. Start web app: python web/app.py

Notes:
- No secrets are included. Use environment variables or a secrets manager for keys.
- This is a skeleton: replace placeholder implementations with your API details and models.
