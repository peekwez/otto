import os

import pandas as pd
from sqlalchemy import create_engine, inspect

# Aiven PostgreSQL connection string from environment
AIVEN_PG_URL = os.getenv("AIVEN_PG_URL", "")
SCHEMA = os.getenv("SCHEMA", "demo")


def connect_engine():
    """Create SQLAlchemy engine for Aiven PostgreSQL."""
    return create_engine(AIVEN_PG_URL)


def load_all_tables() -> dict[str, pd.DataFrame]:
    """
    Load all tables in the schema into a dict of DataFrames.

    Returns:
        dict[str, pd.DataFrame]: Dictionary mapping table names to DataFrames
    """
    engine = connect_engine()
    inspector = inspect(engine)

    table_names = inspector.get_table_names(schema=SCHEMA)

    dfs = {}
    for table in table_names:
        query = f'SELECT * FROM "{SCHEMA}"."{table}"'
        dfs[table] = pd.read_sql(query, con=engine)

    return dfs
