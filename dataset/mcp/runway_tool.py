from analytics.runway import calculate_runway
from load_data import load_all_tables


def runway_tool(args):
    """
    MCP tool wrapper for cash runway calculation.
    
    Args:
        args: Dictionary with optional 'delay_capex_days' key
    
    Returns:
        JSON-serializable dict with runway metrics
    """
    dfs = load_all_tables()
    delay = args.get("delay_capex_days", 0)
    result = calculate_runway(dfs, delay_capex_days=delay)
    return result


tool = {
    "name": "runway.calculate",
    "description": "Calculate cash runway with optional CapEx delay simulation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "delay_capex_days": {
                "type": "integer",
                "description": "Number of days to delay CapEx payments (default: 0)"
            }
        },
        "required": []
    }
}

