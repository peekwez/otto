from analytics.variance import variance_report
from load_data import load_all_tables


def variance_tool(args):
    """
    MCP tool wrapper for variance reporting.
    
    Args:
        args: Dictionary with 'fiscal_quarter' and 'budget_version' keys
    
    Returns:
        JSON-serializable dict with variance rows
    """
    dfs = load_all_tables()
    fiscal_quarter = args.get("fiscal_quarter")
    budget_version = args.get("budget_version")
    
    if not fiscal_quarter or not budget_version:
        return {"error": "fiscal_quarter and budget_version are required"}
    
    result = variance_report(dfs, fiscal_quarter=fiscal_quarter, budget_version=budget_version)
    return result


tool = {
    "name": "variance.report",
    "description": "Generate actual vs budget variance report by fiscal quarter and budget version.",
    "input_schema": {
        "type": "object",
        "properties": {
            "fiscal_quarter": {
                "type": "string",
                "description": "Fiscal quarter (e.g., 'Q1', 'Q2', 'Q3', 'Q4')"
            },
            "budget_version": {
                "type": "string",
                "description": "Budget version (e.g., 'BUDGET_2024')"
            }
        },
        "required": ["fiscal_quarter", "budget_version"]
    }
}

