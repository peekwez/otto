import os

import pandas as pd
from sqlalchemy import create_engine, inspect

# --------------------------------------------------------
# Database connection from environment variables
# Set AIVEN_PG_URL environment variable with your connection string
# --------------------------------------------------------
AIVEN_PG_URL = os.getenv("AIVEN_PG_URL", "")

SCHEMA = os.getenv("SCHEMA", "demo")


def connect_engine():
    """Create SQLAlchemy engine for Aiven PostgreSQL."""
    return create_engine(AIVEN_PG_URL)


def load_all_tables(schema=SCHEMA):
    """
    Load all tables in the schema into a dict of DataFrames.
    """
    engine = connect_engine()
    inspector = inspect(engine)

    table_names = inspector.get_table_names(schema=schema)

    print(f"\n✅ Found {len(table_names)} tables in schema '{schema}':")
    for t in table_names:
        print(f"   - {t}")

    dfs = {}
    for table in table_names:
        query = f'SELECT * FROM "{schema}"."{table}"'
        dfs[table] = pd.read_sql(query, con=engine)

    print("\n✅ Loaded all tables into memory.")
    print("Use: dfs['table_name'] to access a DataFrame.\n")

    return dfs


if __name__ == "__main__":
    dfs = load_all_tables()

    # Display statistics and snippets for all tables
    print("\n" + "=" * 80)
    print("TABLE STATISTICS AND PREVIEWS")
    print("=" * 80 + "\n")

    for table_name, df in dfs.items():
        num_records = len(df)
        num_columns = len(df.columns)

        print(f"📊 Table: {table_name}")
        print(f"   Records: {num_records:,}")
        print(f"   Columns: {num_columns}")
        print(f"   Column names: {', '.join(df.columns.tolist())}")
        print("\n   Preview (first 5 rows):")
        print(df.head().to_string())
        print("\n" + "-" * 80 + "\n")
