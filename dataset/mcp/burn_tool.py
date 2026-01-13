from analytics.burn import burn_by_function
from load_data import load_all_tables


def burn_tool(args):
    """
    MCP tool wrapper for burn by function analysis.
    
    Args:
        args: Dictionary (no required arguments)
    
    Returns:
        JSON-serializable dict with burn by function
    """
    dfs = load_all_tables()
    result = burn_by_function(dfs)
    return result


tool = {
    "name": "burn.by_function",
    "description": "Calculate monthly burn rate by function/cost center.",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

