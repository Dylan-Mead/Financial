import os
from sqlalchemy import create_engine, text, inspect

def get_engine():
    USER = os.getenv("DB_USER")
    PASSWORD = os.getenv("DB_PASSWORD")
    HOST = os.getenv("DB_HOST")
    PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    ADMIN_URL = f"postgresql+psycopg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

    return create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")


def run_sql_file(file_path = None,
                 engine = None):
    if engine is None:
        from sql.run_sql_file import get_engine
        engine = get_engine()
    with open(file_path, 'r') as file:
        sql = file.read()
    with engine.connect() as connection:
        connection.execute(text(sql))
        #connection.commit()
    print(f"Executed SQL file: {file_path}")
    return engine


def describe_table(table_name, schema="public", engine=None):
    """Return column metadata for a PostgreSQL table."""

    if engine is None:
        from sql.run_sql_file import get_engine
        engine = get_engine()
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name, schema=schema)
    primary_key_columns = inspector.get_pk_constraint(
        table_name, schema=schema
    ).get("constrained_columns", [])

    return [
        {
            "column_name": column["name"],
            "type": str(column["type"]),
            "nullable": column["nullable"],
            "default": column["default"],
            "primary_key": column["name"] in primary_key_columns,
        }
        for column in columns
    ]
