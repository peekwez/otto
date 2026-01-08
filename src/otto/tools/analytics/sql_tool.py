import re
import json
from typing import Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from otto.core.settings import get_settings


def execute_analysis_query(
    query: str,
    engine: Engine,
    params: dict[str, Any] | None = None,
    output_format: str = "table"
) -> str:
    """
    Execute a read-only SQL SELECT query for analysis purposes.
    
    Args:
        query: SQL SELECT statement to execute
        engine: SQLAlchemy engine instance
        params: Optional dictionary of query parameters for parameterized queries
        output_format: "table" for human-readable table, "json" for JSON string
    
    Returns:
        String representation of query results
    
    Raises:
        ValueError: If query is not a SELECT statement or contains forbidden keywords
    """
    # Normalize whitespace and convert to uppercase for checking
    normalized = " ".join(query.split()).upper()
    
    # Remove leading comments for the check
    clean_query = re.sub(r'^(\s*--[^\n]*\n|\s*/\*.*?\*/\s*)*', '', normalized, flags=re.DOTALL).strip()
    
    if not clean_query.startswith('SELECT'):
        raise ValueError("Only SELECT statements are allowed")
    
    # Forbidden keywords that could cause side effects
    forbidden_patterns = [
        r'\bINSERT\b',
        r'\bUPDATE\b',
        r'\bDELETE\b',
        r'\bDROP\b',
        r'\bCREATE\b',
        r'\bALTER\b',
        r'\bTRUNCATE\b',
        r'\bGRANT\b',
        r'\bREVOKE\b',
        r'\bEXEC\b',
        r'\bEXECUTE\b',
        r'\bCALL\b',
        r'\bINTO\s+(?:OUTFILE|DUMPFILE)\b',
        r'\bSET\b',
        r'\bMERGE\b',
        r'\bREPLACE\b',
    ]
    
    for pattern in forbidden_patterns:
        if re.search(pattern, normalized):
            raise ValueError(f"Query contains forbidden keyword matching: {pattern}")
    
    # Execute query
    with engine.connect() as conn:
        result = conn.execute(text(query), parameters=params or {})
        columns = list(result.keys())
        rows = result.fetchall()
    
    # Handle empty results
    if not rows:
        return "No results found."
    
    # Format output
    if output_format == "json":
        data = [dict(zip(columns, row)) for row in rows]
        return json.dumps(data, indent=2, default=str)
    
    # Default: formatted table
    return _format_as_table(columns, rows)


def _format_as_table(columns: list[str], rows: list[tuple]) -> str:
    """Format results as an ASCII table."""
    # Convert all values to strings
    str_rows = [[str(val) if val is not None else "NULL" for val in row] for row in rows]
    
    # Calculate column widths
    widths = [len(col) for col in columns]
    for row in str_rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))
    
    # Build table
    separator = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header = "|" + "|".join(f" {col.ljust(widths[i])} " for i, col in enumerate(columns)) + "|"
    
    lines = [separator, header, separator]
    for row in str_rows:
        line = "|" + "|".join(f" {val.ljust(widths[i])} " for i, val in enumerate(row)) + "|"
        lines.append(line)
    lines.append(separator)
    lines.append(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")
    
    return "\n".join(lines)


def create_readonly_engine(connection_string: str) -> Engine:
    """Create a SQLAlchemy engine configured for read-only access."""
    settings = get_settings()
    return create_engine(
        settings.postgres.url.get_secret_value(),
        execution_options={"isolation_level": "AUTOCOMMIT"},
        pool_pre_ping=True
    )