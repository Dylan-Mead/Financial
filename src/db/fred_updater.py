# this script will mostly mirror what was done in fred_updater.ipynb
#the purpose will be to check if our fred data in sql data should be updated and if so grab fresh data and append to the sql tables
#intended to be run daily via cron to keep fred tables up to date (does not do the initial 1990 backfill)
import os
import re
from pathlib import Path
from time import sleep

import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred
from sqlalchemy import text

from db.pgsql import pgsql

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRED_IDS_FILE = PROJECT_ROOT / "documentation" / "fred_ids.txt"

VALID_SERIES_ID = re.compile(r"^[A-Za-z0-9_]+$")

DATE_DELTA_BY_FREQUENCY = {
    'D': pd.Timedelta(days=1),
    'W': pd.Timedelta(weeks=1),
    'M': pd.Timedelta(days=30),
    'Q': pd.Timedelta(days=91),
}


def convert_series_to_df(series: pd.Series) -> pd.DataFrame:
    df = series.to_frame().reset_index()
    df.columns = ['date', 'value']
    return df


def load_fred_ids() -> list[str]:
    with open(FRED_IDS_FILE, "r") as file:
        return [line.strip() for line in file.readlines() if line.strip()]


def update_fred_tables():
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise ValueError(
            f"FRED_API_KEY must be set in {PROJECT_ROOT / '.env'} or the environment."
        )
    fred = Fred(api_key=api_key)

    db = pgsql()
    engine = db.get_engine()

    today = pd.Timestamp.today()
    today_formatted = today.strftime('%Y-%m-%d')

    with engine.begin() as connection:
        for series_id in load_fred_ids():
            #table names can't be parameterized, so validate against an allowlist pattern first
            if not VALID_SERIES_ID.match(series_id):
                print(f"Skipping invalid series id: {series_id}")
                continue

            table_name = series_id.lower()
            max_date_query = text(f"SELECT MAX(date) FROM {table_name}")
            max_date = pd.Timestamp(connection.execute(max_date_query).scalar())
            print(f"Max date for {series_id}: {max_date}")

            frequency_query = text(
                "SELECT frequency_short FROM fred_series_info WHERE id = :series_id LIMIT 1"
            )
            frequency_short = connection.execute(frequency_query, {"series_id": series_id}).scalar()
            print(f"Frequency short for {series_id}: {frequency_short}")

            next_read_day = max_date + DATE_DELTA_BY_FREQUENCY[frequency_short]
            print(f"Next read day for {series_id}: {next_read_day}")

            if next_read_day > today:
                continue

            print(f"Fetching data for {series_id} starting from {next_read_day}")
            temp_fresh_data = fred.get_series(
                series_id,
                observation_start=next_read_day.strftime('%Y-%m-%d'),
                observation_end=today_formatted,
            )
            if temp_fresh_data.empty:
                print(f"No new data returned for {series_id}, skipping")
                continue

            df_to_append = convert_series_to_df(temp_fresh_data)
            df_to_append = df_to_append[df_to_append['date'] > max_date]
            if df_to_append.empty:
                print(f"No new data to append for {series_id}, skipping")
                continue

            db.set_table_name(table_name)
            db.set_pdf(df_to_append)
            db.write_pdf_to_sql(if_exists='append')
            sleep(1)


if __name__ == "__main__":
    update_fred_tables()
