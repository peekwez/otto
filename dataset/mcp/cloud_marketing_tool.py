from analytics.cloud_marketing import cloud_marketing_breakdown
from load_data import load_all_tables


def cloud_marketing_tool(args):
    """
    MCP tool wrapper for cloud and marketing spend breakdown.
    
    Args:
        args: Dictionary with 'month' key
    
    Returns:
        JSON-serializable dict with cloud and marketing breakdown
    """
    dfs = load_all_tables()
    month = args.get("month")
    
    if not month:
        return {"error": "month is required (format: 'YYYY-MM')"}
    
    result = cloud_marketing_breakdown(dfs, month=month)
    return result


tool = {
    "name": "cloud_marketing.breakdown",
    "description": "Generate cloud and marketing spend breakdown for a specific month.",
    "input_schema": {
        "type": "object",
        "properties": {
            "month": {
                "type": "string",
                "description": "Fiscal month (format: 'YYYY-MM', e.g., '2024-01')"
            }
        },
        "required": ["month"]
    }
}

