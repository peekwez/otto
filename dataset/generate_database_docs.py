import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text

# Use the SAME connection string from environment variables
AIVEN_PG_URL = os.getenv("AIVEN_PG_URL", "")
SCHEMA = os.getenv("SCHEMA", "demo")


def connect_engine():
    return create_engine(AIVEN_PG_URL)


def get_table_columns(engine, schema, table):
    """Get column information for a table."""
    query = text("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = :schema AND table_name = :table
        ORDER BY ordinal_position
    """)
    return pd.read_sql(query, engine, params={"schema": schema, "table": table})


def get_foreign_keys(engine, schema):
    """Get foreign key relationships in the schema."""
    query = text("""
        SELECT
            tc.table_name AS from_table,
            kcu.column_name AS from_column,
            ccu.table_name AS to_table,
            ccu.column_name AS to_column,
            tc.constraint_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = :schema
    """)
    return pd.read_sql(query, engine, params={"schema": schema})


def get_primary_keys(engine, schema, table):
    """Get primary key columns for a table."""
    query = text("""
        SELECT column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_schema = :schema
            AND tc.table_name = :table
    """)
    result = pd.read_sql(query, engine, params={"schema": schema, "table": table})
    return set(result["column_name"].tolist()) if not result.empty else set()


def generate_erd_mermaid(engine, schema, tables):
    """Generate Mermaid ERD diagram."""
    lines = []
    lines.append("\n## Entity Relationship Diagram (ERD)\n")
    lines.append("```mermaid\n")
    lines.append("erDiagram\n")

    # Get all foreign keys
    fks_df = get_foreign_keys(engine, schema)

    # Build table structures
    table_info = {}
    for table in tables:
        cols_df = get_table_columns(engine, schema, table)
        pks = get_primary_keys(engine, schema, table)

        table_info[table] = {"columns": cols_df, "primary_keys": pks}

    # Generate table definitions
    for table in sorted(tables):
        cols_df = table_info[table]["columns"]
        pks = table_info[table]["primary_keys"]

        lines.append(f"    {table} {{\n")
        for _, col in cols_df.iterrows():
            col_name = col["column_name"]
            col_type = col["data_type"]
            is_nullable = col["is_nullable"] == "YES"
            is_pk = col_name in pks

            # Format column display
            prefix = "PK " if is_pk else ""
            suffix = "" if is_nullable else " NOT NULL"
            # Shorten some data type names for readability
            type_map = {
                "character varying": "varchar",
                "integer": "int",
                "double precision": "float",
                "timestamp without time zone": "timestamp",
                "timestamp with time zone": "timestamptz",
            }
            display_type = type_map.get(col_type, col_type)
            lines.append(f"        {prefix}{col_name} {display_type}{suffix}\n")
        lines.append("    }\n")

    # Generate relationships
    if not fks_df.empty:
        lines.append("\n")
        for _, fk in fks_df.iterrows():
            from_table = fk["from_table"]
            to_table = fk["to_table"]
            from_col = fk["from_column"]
            to_col = fk["to_column"]

            # Use "||--o{" for one-to-many, "||--||" for one-to-one
            # For fact tables, usually many-to-one with dimensions
            relationship = "||--o{" if from_table.startswith("fact_") else "}o--||"
            lines.append(
                f'    {from_table} {relationship} {to_table} : "{from_col} -> {to_col}"\n'
            )

    lines.append("```\n")
    return "".join(lines)


def generate_markdown(output_path="database_documentation.md"):
    engine = connect_engine()
    inspector = inspect(engine)

    tables = inspector.get_table_names(schema=SCHEMA)

    lines = []
    lines.append("# CFO Data Model Documentation\n")
    lines.append(
        "This document describes each table in the `demo` schema and shows sample rows.\n"
    )

    for table in tables:
        lines.append(f"\n## {table}\n")

        # Identify type by naming convention
        if table.startswith("dim_"):
            lines.append("**Type:** Dimension table (business entities)\n")
        elif table.startswith("fact_"):
            lines.append("**Type:** Fact table (numeric / time-based records)\n")
        else:
            lines.append("**Type:** Supporting / KPI / Reporting layer\n")

        # Load small preview
        query = f'SELECT * FROM "{SCHEMA}"."{table}" LIMIT 5'
        df_sample = pd.read_sql(query, engine)

        lines.append("**Example rows:**\n")
        lines.append(df_sample.to_markdown(index=False) + "\n")

    # Add ERD at the end
    lines.append(generate_erd_mermaid(engine, SCHEMA, tables))

    Path(output_path).write_text("".join(lines), encoding="utf-8")
    print(f"✅ Documentation written to {output_path}")


if __name__ == "__main__":
    generate_markdown("database_documentation_full.md")
