from typing import Any

import pandas as pd
from mcp.server.fastmcp import Context, FastMCP

from otto.core.logging import get_logger
from otto.tools.analytics.burn import burn_by_function
from otto.tools.analytics.runway import calculate_runway
from otto.tools.analytics.variance import variance_report
from otto.tools.analytics.accounting_top_accounts import accounting_top_accounts
from otto.tools.analytics.accounting_trends import accounting_monthly_trends
from otto.tools.analytics.payroll_departments import payroll_by_department
from otto.tools.analytics.workforce_planning import workforce_planning
from otto.tools.analytics.workforce_forecasting import workforce_forecasting
from otto.tools.analytics.income_statement import income_statement
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
    Get the list of available datasets available for the Connectiv Demo (e.g Sample Financial Data Or Couqley Data).

    Args:
        ctx (Context): MCP context

    Returns:
        dict[str, str]: Dictionary with dataset names and their markdown representations
    """
    return {key: df.head().to_markdown() for key, df in _dfs.items()}


@mcp.tool(name="BurnByFunction")
def burn_by_function_tool(ctx: Context) -> dict[str, Any]:  # type: ignore
    """
    Calculate burn rate using Financial Sample Data.

    Args:
        ctx (Context): MCP context

    Returns:
        dict[str, Any]: Dictionary with burn by function information
    """
    result = burn_by_function(_dfs)
    return result


@mcp.tool(name="Runway")
def runway_tool(delay_capex_days: int, ctx: Context) -> dict[str, Any]:  # type: ignore
    """
    Calculate runway based on burn rate and cash balance using Financial Sample Data.

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
    Generate actual vs budget variance report by fiscal quarter and budget version using Financial Sample Data.

    Args:
        fiscal_quarter (str): Fiscal quarter (e.g., "Q1", "Q2")
        budget_version (str): Budget version (e.g., "BUDGET_2024")
        ctx (Context): MCP context

    Returns:
        dict[str, Any]: Dictionary with variance report information
    """
    result = variance_report(_dfs, fiscal_quarter, budget_version)
    return result


@mcp.tool(name="AccountingTopAccounts")
def accounting_top_accounts_tool(ctx: Context) -> dict[str, Any]:  # type: ignore
    """
    Generate accounting top accounts report using Couqley Data.

    Args:
        ctx (Context): MCP context

    Returns:
        dict[str, Any]: Dictionary with accounting top accounts report information
    """
    result = accounting_top_accounts(_dfs)
    return result

@mcp.tool(name="AccountingTrends")
def accounting_trends_tool(ctx: Context) -> dict[str, Any]:  # type: ignore
    """
    Generate accounting trends report using Coqley Data.

    Args:
        ctx (Context): MCP context

    Returns:
        dict[str, Any]: Dictionary with accounting trends report information
    """
    result = accounting_monthly_trends(_dfs)
    return result

@mcp.tool(name="PayrollDepartments")
def payroll_departments_tool(ctx: Context) -> dict[str, Any]:  # type: ignore
    """
    Generate payroll departments report using Couqley Data.

    Args:
        ctx (Context): MCP context

    Returns:
        dict[str, Any]: Dictionary with payroll departments report information
    """
    result = payroll_by_department(_dfs)
    return result

@mcp.tool(name="WorkforcePlanning")
def workforce_planning_tool(ctx: Context) -> dict[str, Any]:  # type: ignore
    """
    Generate workforce planning report using Couqley Data.

    Args:
        ctx (Context): MCP context

    Returns:
        dict[str, Any]: Dictionary with workforce planning report information
    """
    result = workforce_planning(_dfs)
    return result

@mcp.tool(name="WorkforceForecasting")
def workforce_forecasting_tool(ctx: Context) -> dict[str, Any]:  # type: ignore
    """
    Generate workforce forecasting report using Couqley Data.

    Args:
        ctx (Context): MCP context

    Returns:
        dict[str, Any]: Dictionary with workforce forecasting report information
    """
    result = workforce_forecasting(_dfs)
    return result

@mcp.tool(name="IncomeStatement")
def income_statement_tool(ctx: Context) -> dict[str, Any]:  # type: ignore
    """
    Generate income statement report using Couqley Data.

    Args:
        ctx (Context): MCP context

    Returns:
        dict[str, Any]: Dictionary with income statement report information
    """
    result = income_statement(_dfs)
    return result