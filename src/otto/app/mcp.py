from typing import Any

import pandas as pd
from mcp.server.fastmcp import Context, FastMCP

from otto.core.logging import get_logger
from otto.tools.analytics.burn import burn_by_function
from otto.tools.analytics.runway import calculate_runway
from otto.tools.analytics.variance import variance_report
from otto.tools.utils import load_all_tables

_dfs: dict[str, pd.DataFrame] = {}
_logger = get_logger(__name__)


def initialize_datasets() -> None:
    global _dfs
    _dfs = load_all_tables()
    _logger.info("Loaded all tables for MCP.")


mcp = FastMCP(
    name="cfo_mcp",
    instructions="A simple CFO plugin for FastMCP.",
)


@mcp.tool(name="Datasets")
def get_datasets_tool(ctx: Context) -> dict[str, str]:  # type: ignore
    """
    Get the list of available datasets.

    Args:
        ctx (Context): MCP context

    Returns:
        dict[str, str]: Dictionary with dataset names and their markdown representations
    """
    return {key: df.head().to_markdown() for key, df in _dfs.items()}


@mcp.tool(name="BurnByFunction")
def burn_by_function_tool(ctx: Context) -> dict[str, Any]:  # type: ignore
    result = burn_by_function(_dfs)
    return result


@mcp.tool(name="Runway")
def runway_tool(delay_capex_days: int, ctx: Context) -> dict[str, Any]:  # type: ignore
    """
    Calculate runway based on burn rate and cash balance.

    Args:
        delay_capex_days (int): Number of days to delay CapEx payments
        ctx (Context): MCP context

    Returns:
        dict[str, Any]: Dictionary with runway information
    """
    result = calculate_runway(_dfs, delay_capex_days=delay_capex_days)
    return result


@mcp.tool(name="VarianceReport")
def variance_report_tool(
    fiscal_quarter: str,
    budget_version: str,
    ctx: Context,  # type: ignore
) -> dict[str, Any]:  # type: ignore
    """
    Generate actual vs budget variance report by fiscal quarter and budget version.

    Args:
        fiscal_quarter (str): Fiscal quarter (e.g., "Q1", "Q2")
        budget_version (str): Budget version (e.g., "BUDGET_2024")
        ctx (Context): MCP context

    Returns:
        dict[str, Any]: Dictionary with variance report information
    """
    result = variance_report(_dfs, fiscal_quarter, budget_version)
    return result
