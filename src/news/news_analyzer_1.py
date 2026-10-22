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
lookback_hours = 1



def get_api_key_secret():
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise ValueError(
            "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in "
            f"{PROJECT_ROOT / '.env'} or the environment."
        )
    return api_key, secret_key


def get_request_headers():
    api_key, secret_key = get_api_key_secret()
    return {
        "accept": "application/json",
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
    }


def get_ticker_file(folder, file_name):
    ticker_file = PROJECT_ROOT / folder / file_name
    if not ticker_file.is_file():
        raise FileNotFoundError(
            f"Could not find project file: {ticker_file}"
        )
    return ticker_file


def get_symbols_from_file(ticker_file):
    return list(
        dict.fromkeys(
            line.strip().upper()
            for line in ticker_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    )


ENDPOINT = "https://data.alpaca.markets/v1beta1/news"
PAGE_SIZE = 50
SYMBOLS_PER_REQUEST = 40
LOOKBACK = timedelta(hours=lookback_hours)

end_time = datetime.now(timezone.utc)
start_time = end_time - LOOKBACK




def to_rfc3339(value):
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def get_with_retry(headers, params):
    for attempt in range(1, MAX_REQUEST_ATTEMPTS + 1):
        error = None
        try:
            response = requests.get(ENDPOINT, headers=headers, params=params, timeout=30)
            if response.status_code not in RETRYABLE_STATUS_CODES:
                response.raise_for_status()
                return response
            error = requests.HTTPError(
                f"Alpaca returned retryable HTTP {response.status_code}",
                response=response,
            )
        except (requests.ConnectionError, requests.Timeout) as request_error:
            error = request_error

        if attempt == MAX_REQUEST_ATTEMPTS:
            raise RuntimeError(
                f"Alpaca news request failed after {MAX_REQUEST_ATTEMPTS} attempts."
            ) from error

        delay = INITIAL_RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
        print(
            f"Alpaca news request failed ({error}); retrying in {delay} seconds "
            f"({attempt}/{MAX_REQUEST_ATTEMPTS})."
        )
        time.sleep(delay)


def retrieve_articles(symbols, headers):
    news_by_id = {}
    request_count = 0

    for offset in range(0, len(symbols), SYMBOLS_PER_REQUEST):
        symbol_batch = symbols[offset : offset + SYMBOLS_PER_REQUEST]
        page_token = None

        while True:
            params = {
                "symbols": ",".join(symbol_batch),
                "start": to_rfc3339(start_time),
                "end": to_rfc3339(end_time),
                "sort": "desc",
                "limit": PAGE_SIZE,
                "include_content": "false",
            }
            if page_token:
                params["page_token"] = page_token

            response = get_with_retry(headers, params)
            payload = response.json()
            if not isinstance(payload, dict) or not isinstance(payload.get("news"), list):
                raise ValueError("Unexpected Alpaca news response: expected an object with a 'news' list.")

            request_count += 1
            for article in payload["news"]:
                article_id = article.get("id")
                if article_id is None:
                    raise ValueError("Alpaca returned a news article without an ID.")

                if article_id not in news_by_id:
                    news_by_id[article_id] = article
                else:
                    known_symbols = set(news_by_id[article_id].get("symbols") or [])
                    known_symbols.update(article.get("symbols") or [])
                    news_by_id[article_id]["symbols"] = sorted(known_symbols)

            page_token = payload.get("next_page_token")
            if not page_token:
                break
            time.sleep(0.7)

        if offset + SYMBOLS_PER_REQUEST < len(symbols):
            time.sleep(0.7)

    articles = list(news_by_id.values())
    print(f"Received {len(articles)} unique articles in {request_count} API requests.")
    return articles




def fix_news_list_from_raw(articles: list[dict]) -> list[dict]:
    with ASSETS_US_EQUITY_FILE.open(encoding="utf-8") as file:
        assets_us_equity = json.load(file)
    assets_us_equity_df = pd.DataFrame(assets_us_equity)
    
    for news in articles:
        tickers = news.get('symbols', [])
        company_dict = {}
        for ticker in tickers:
            try:
                name = assets_us_equity_df.loc[assets_us_equity_df['symbol'] == ticker, 'name'].values[0]
            except IndexError:
                name = None
            company_dict[ticker] = name
        message = "HEADLINE: " + str(news.get('headline', '')) + "\nSUMMARY: " + str(news.get('summary', ''))  # if summary is not nan then message is summary, else message is headline
        while "\n\n" in message:
            message = message.replace("\n\n", "\n")

        news['message'] = message
        news['company_names'] = company_dict
    return articles


#with open('../../tests/assets_us_equity.json', 'r') as file:
#    assets_us_equity = json.load(file)
#assets_us_equity_df = pd.DataFrame(assets_us_equity)

def fix_news_list(news_list):
    with ASSETS_US_EQUITY_FILE.open(encoding="utf-8") as file:
        assets_us_equity = json.load(file)
    assets_us_equity_df = pd.DataFrame(assets_us_equity)
    
    for news in news_list:
        tickers = ast.literal_eval(news.get('tickers', []))
        company_dict = {}
        for ticker in tickers:
            try:
                name = assets_us_equity_df.loc[assets_us_equity_df['symbol'] == ticker, 'name'].values[0]
            except IndexError:
                name = None
            company_dict[ticker] = name
        message = "HEADLINE: " + str(news.get('headline', '')) + "\nSUMMARY: " + str(news.get('summary', ''))  # if summary is not nan then message is summary, else message is headline
        while "\n\n" in message:
            message = message.replace("\n\n", "\n")

        news['message'] = message
        news['company_names'] = company_dict
    return news_list


def build_scores_schema(tickers) -> dict:
    """JSON schema requiring one score in [-1, 1] for every ticker."""
    return {
        'type': 'object',
        'properties': {
            t: {'type': 'number', 'minimum': -1.0, 'maximum': 1.0} for t in tickers
        },
        'required': list(tickers),
        'additionalProperties': False,
    }


class HeadlineSentimentAnalyzer:
    def __init__(
        self,
        model: str = 'qwen3:8b',
        keep_alive: str = '10m',
        system_prompt_in_model: bool = False,
        temperature: float = 0.0,
    ):
        self.model = model
        self.keep_alive = keep_alive
        self.system_prompt_in_model = system_prompt_in_model
        self.temperature = temperature
        #self.system_prompt = (
        #    "You are an expert financial analyst. Your task is to look at a news message "
        #    "and judge its sentiment regarding each of the given publicly traded companies. "
        #    "You will be given a JSON dictionary (company_names) that matches ticker symbols to company names, "
        #    "and the news message. "
        #    "Provide a rating score for every ticker strictly between -1.0 (very bearish/negative) and "
        #    "+1.0 (very bullish/positive). Highly neutral or purely factual announcements "
        #    "without clear financial impact, or companies not meaningfully discussed, should be given 0.0. "
        #    "Return a JSON object with the ticker symbols as keys and their sentiment scores as values."
        #)
        self.system_prompt = ("""You are an expert financial analyst. 
            Your task is to analyze a news message and judge its sentiment regarding specific publicly traded companies. 

            INPUTS PROVIDED:
            1. `company_names`: A JSON dictionary mapping ticker symbols to company names.
            2. `news_message`: The text text to be analyzed.

            SCORING CRITERIA:
            Assign a sentiment score strictly between -1.0 and +1.0 for EVERY ticker provided in the `company_names` dictionary.
            * Scores can be a decimal from -1 to +1 such as -0.75, 0.31, 0.89, etc.
            * +1.0 = Very Bullish / Strongly Positive (e.g., massive earnings beat, major acquisition, large new government contract)
            * +0.5 = Moderately Bullish / Positive (e.g., incremental contract win, steady growth)
            *  0.0 = Neutral, purely factual announcements without immediate financial impact, mixed news, or if the company is merely mentioned without meaningful discussion.
            * -0.5 = Moderately Bearish / Negative (e.g., slight earnings miss, executive departure)
            * -1.0 = Very Bearish / Strongly Negative (e.g., severe regulatory fines, catastrophic fraud, loss of government contract)
            * These are just examples. If you think it is appropriate to assign a different score, from -1 to +1, based on the context, you may do so.
            * choose scores from [-1, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

            STRICT OUTPUT CONSTRAINTS:
            - You must return ONLY a raw JSON object where keys are the exact ticker symbols from `company_names` and values are the numerical sentiment scores (floats).
            - Do not include markdown blocks like ```json ... ```.
            - Do not include any introductory text, explanations, or postscript commentary. 
            - If a ticker from `company_names` is not mentioned or relevant to the text, you must still include it in the JSON object with a score of 0.0.

            OUTPUT TEMPLATE:
            {
            "TICKER1": 0.0,
            "TICKER2": 0.8,
            "TICKER3": -0.2,
            }
            """)
        self.custom_model = 'fin_news_analyzer'
        ollama.create(model = self.custom_model,
                      from_ = self.model,
                      system = self.system_prompt,
                      parameters={'temperature': self.temperature},
                      )

    def analyze_headline_sentiment(self, news_data: dict) -> dict:
        """Return a copy of the news dict with a 'scores' dict {ticker: score}."""
        company_names = news_data.get('company_names') or {}
        result = dict(news_data)
        if not company_names:
            result['scores'] = {}
            return result

        user_content = (
            f"company_names: {json.dumps(company_names, indent=2)}\n"
            f"message: {news_data.get('message', '')}"
        )
        messages = [{'role': 'user', 'content': user_content}]
        #if not self.system_prompt_in_model:
        #    messages.insert(0, {'role': 'system', 'content': self.system_prompt})

        try:
            response = ollama.chat(
                model=self.custom_model,
                messages=messages,
                format=build_scores_schema(list(company_names)),
                think=False,
                options={'temperature': 0.0},
                keep_alive=self.keep_alive,
            )
            content = response.get('message', {}).get('content', '').strip()
            if not content:
                raise RuntimeError(f"Ollama returned empty content: {response!r}")

            raw = json.loads(content)
            result['scores'] = {
                t: max(-1.0, min(1.0, float(raw.get(t, 0.0)))) for t in company_names
            }
            return result

        except ollama.ResponseError as e:
            raise RuntimeError(f"Ollama API error: {e.error}") from e

    def analyze_headlines(self, news_items: list[dict]) -> list[dict]:
        """Analyze every news item; return the batch with 'scores' added to each."""
        total = len(news_items)
        results = []
        for i, news in enumerate(news_items, start=1):
            print(f"analyzing news {i}/{total}: {news.get('headline', '')}")
            results.append(self.analyze_headline_sentiment(news))
        return results

def explode_scores(analized_list: list[dict]) -> pd.DataFrame:
    df_temp = pd.DataFrame(analized_list)
    df_temp['scores'] = df_temp['scores'].apply(lambda d: list(d.items()))
    df_temp = df_temp.explode('scores')
    df_temp[['ticker', 'score']] = pd.DataFrame(df_temp['scores'].tolist(), index=df_temp.index)
    return df_temp.reset_index()


def clean_columns(df_in: pd.DataFrame) -> pd.DataFrame:
    df_temp = df_in.copy()
    df_temp['timestamp'] = pd.to_datetime(df_temp['updated_at'])
    df_temp['unique_id'] = df_temp['id'].astype(str) + '-' + df_temp['ticker']
    df_temp = df_temp[df_temp['score'].notna()]
    df_temp = df_temp[df_temp['score'] != 0]
    return df_temp[['id', 'unique_id', 'url', 'timestamp', 'ticker', 'score', 'message']]





def update_news_tables():
    ticker_file = get_ticker_file("documentation", "alpaca_tickers.txt")
    symbols = get_symbols_from_file(ticker_file)
    articles = retrieve_articles(symbols, get_request_headers())
    if not articles:
        print("No new articles in the lookback window; nothing to update.")
        return
    fixed_articles = fix_news_list_from_raw(articles)
    hsa = HeadlineSentimentAnalyzer()
    analized = hsa.analyze_headlines(fixed_articles)
    df_expanded = explode_scores(analized)
    df_expanded_cleaned = clean_columns(df_expanded)
    if df_expanded_cleaned.empty:
        print("No scored articles to write; nothing to update.")
        return
    db = pgsql()
    db.set_table_name('newstest')
    db.date_column_name = 'timestamp'
    db.set_pdf(df_expanded_cleaned)
    if not db.update_sql_from_pdf():
        raise RuntimeError("Failed to write news scores to 'newstest'")

if __name__ == "__main__":
    update_news_tables()
