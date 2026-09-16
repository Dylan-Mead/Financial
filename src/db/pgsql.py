#Here we will have a class for interacting with the postgresql db

import os
#import gc
#from dotenv import load_dotenv
#from sqlalchemy.exc import ProgrammingError
from sqlalchemy import create_engine, text, inspect
import pandas as pd
#import cudf


#create a class for interacting with the postgresql db

class pgsql:
    def __init__(self):
        USER = os.getenv("DB_USER")
        PASSWORD = os.getenv("DB_PASSWORD")
        HOST = os.getenv("DB_HOST")
        PORT = os.getenv("DB_PORT")
        DB_NAME = os.getenv("DB_NAME")
        ADMIN_URL = f"postgresql+psycopg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
        
        self.engine = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")#, echo=True)
        self.inspector = inspect(self.engine)
        self.table_name = ""
        self.pdf = None
    #    self.cudf = None

    def get_inspector(self):
        return self.inspector

    def refresh_inspector(self):
        try:
            self.inspector = inspect(self.engine)
            return True
        except Exception as e:
            print(f"Error refreshing inspector: {e}")
            return False

    def set_table_name(self, table_name = ""):
        try:
            self.table_name = table_name
            return True
        except Exception as e:
            print(f"Error setting table name: {e}")
            return False

    def get_table_name(self):
        return self.table_name

    def get_tables(self):
        return self.inspector.get_table_names()

    def get_sql_description(self, table_name = "", schema = "public"):
        if table_name == "":
            table_name = self.table_name
        columns = self.inspector.get_columns(table_name, schema=schema)
        primary_key_columns = self.inspector.get_pk_constraint(table_name, schema=schema).get("constrained_columns", [])
        return[
            {
                "name": column["name"],
                "type": column["type"],
                "nullable": column["nullable"],
                "default": column["default"],
                "primary_key": column["name"] in primary_key_columns
            } for column in columns
        ]
    
    def set_pdf(self, pdf = pd.DataFrame()):
        try:
            self.pdf = pdf
            return True
        except Exception as e:
            print(f"Error setting Pandas DataFrame: {e}")
            return False

    def get_pdf(self):
        return self.pdf

    def clear_pdf(self):
        try:
            self.pdf = None
            return True
        except Exception as e:
            print(f"Error clearing Pandas DataFrame: {e}")
            return False

    def clear_dataframes(self):
        try:
            self.clear_pdf()
            return True
        except Exception as e:
            print(f"Error clearing Pandas DataFrame: {e}")
            return False

    def check_pdf_compatability(self):
        #Check if columns names and types of pandas dataframe and sql table are compatible
        if self.pdf is None:
            return False
        sql_description = self.get_sql_description()
        sql_columns = {col["name"]: col["type"] for col in sql_description}
        for col in self.pdf.columns:
            if col not in sql_columns:
                return False
            if not pd.api.types.is_dtype_equal(self.pdf[col].dtype, sql_columns[col].python_type):
                return False
        return True

    def write_pdf_to_sql(self):
        try:
            if not self.check_pdf_compatability():
                raise ValueError("PDF is not compatible with SQL table")
            self.pdf.to_sql(self.table_name, self.engine, if_exists="replace", index=False)
            return True
        except Exception as e:
            print(f"Error writing Pandas DataFrame to SQL: {e}")
            return False

    def get_table_as_pdf(self):
        return self.pdf


    #next we need a function that can return a subset of the sql table using a SQL query as a string
    def return_query_as_df(self, query):
        return pd.read_sql_query(query, self.engine)

    def get_table_subset_as_pdf_with_where_clauses(self, where_clauses={}):
        query = "SELECT * FROM " + self.table_name + " WHERE " + " AND ".join([f"{k} = {v}" for k, v in where_clauses.items()])
        return pd.read_sql_query(query, self.engine)