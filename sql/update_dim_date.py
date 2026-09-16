#this is used to add another year to the dim_date table

import pandas as pd
from sqlalchemy import create_engine, text, inspect

def get_year_dim_date_df(year, start_id):
    #dates = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31', tz='UTC')
    dates = pd.date_range(start=f"{year}-01-01 00:00:00", end=f"{year}-12-31 23:59:00", freq="min", tz="UTC")
    df = pd.DataFrame()
    df['Date'] = dates
    df['year'] = dates.year
    df['quarter'] = dates.quarter
    df['month'] = dates.month
    df['day_of_month'] = dates.day
    df['hour'] = dates.hour
    df['minute'] = dates.minute
    df['id'] = range(start_id, start_id + len(df))
    return df


def write_dataframe_to_table(dataframe=pd.DataFrame(),#as created by get_year_dim_date_df
                             table_name=None,#name of table in sql db
                             schema="public",#should be public
                             engine=None,#as made by sqlalchemy.create_engine
                             chunksize=None,):#chunk size should be <= floor((2**16-1) / len(dataframe.columns))
    
    """Append a dataframe to a SQL table and return the number of rows written."""
    #import pandas as pd
    #from sqlalchemy import inspect
    if not chunksize:
        chunksize = min((2**16 - 1) // len(dataframe.columns) - 1, 8000)
    chunksize = int(chunksize)
    if dataframe.empty:
        return 0

    table_columns = [
        column["name"]
        for column in inspect(engine).get_columns(table_name, schema=schema)
    ]
    source = dataframe.copy()

    if "Date" in source.columns and "date" not in source.columns:
        source = source.rename(columns={"Date": "date"})
    if "date" not in source.columns:
        raise ValueError("The dataframe must contain a Date or date column")

    source["date"] = pd.to_datetime(source["date"])
    if source["date"].isna().any():
        raise ValueError("The date column contains null values")

    if "id" not in source.columns:
        source["id"] = source["date"].dt.strftime("%Y%m%d%H%M").astype("int64")

    if source["id"].duplicated().any():
        raise ValueError("The dataframe contains duplicate primary-key values")

    missing_columns = set(table_columns) - set(source.columns)
    if missing_columns:
        raise ValueError(
            f"The dataframe is missing required table columns: {sorted(missing_columns)}"
        )

    source = source[table_columns]
    with engine.begin() as connection:
        source.to_sql(
            table_name,
            con=connection,
            schema=schema,
            if_exists="append",
            index=False,
            chunksize=chunksize,
            method="multi",
        )

    return len(source)

#def update_dim_date(dataframe=pd.DataFrame(),