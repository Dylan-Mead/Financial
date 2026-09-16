import pandas as pd
import sqlalchemy as sqla
from fredapi import Fred
import keyring

class Table:
    def __init__(self, name):#, engine):
        self.name = name
        #self.engine = engine

    def to_dataframe(self):
        service = "fred"
        api_key = keyring.get_password(service, "api_key")
        Fred(api_key=api_key)
        query = f"SELECT * FROM {self.name}"
        return pd.read_sql(query, self.engine)
        fred = Fred(api_key=api_key)
        unemployment_data = fred.get_series('UNRATE', observation_start='2023-01-01', observation_end='2026-07-31')