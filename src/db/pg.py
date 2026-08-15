"""Postgres helpers using SQLAlchemy.

Keep models simple here; replace with your application's models or use Alembic for migrations.
"""
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Float, DateTime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
import pandas as pd
from ..config import DATABASE_URL

metadata = MetaData()

# Simple table definition for collected data
collected_data = Table(
    "collected_data",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("symbol", String, nullable=False),
    Column("ts", DateTime, nullable=False),
    Column("price", Float, nullable=True),
    Column("raw", String, nullable=True),
)


def get_engine(url: str | None = None) -> Engine:
    url = url or DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    return create_engine(url)


def init_db(engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    metadata.create_all(engine)


def insert_rows(rows: list[dict], engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    with engine.begin() as conn:
        try:
            conn.execute(collected_data.insert(), rows)
        except SQLAlchemyError:
            raise


def query_to_dataframe(limit: int = 100, engine: Engine | None = None) -> pd.DataFrame:
    engine = engine or get_engine()
    with engine.connect() as conn:
        df = pd.read_sql_table("collected_data", conn, columns=None)
    if limit:
        return df.tail(limit)
    return df

if __name__ == "__main__":
    e = get_engine()
    init_db(e)
    print("Initialized DB (or already exists)")
