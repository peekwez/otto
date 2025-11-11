from analytics.slides import generate_kpi_slide
from load_data import load_all_tables


def slides_tool(args):
    """
    MCP tool wrapper for KPI slide generation.
    
    Args:
        args: Dictionary with 'month' key
    
    Returns:
        JSON-serializable dict with KPI values and narrative
    """
    dfs = load_all_tables()
    month = args.get("month")
    
    if not month:
        return {"error": "month is required (format: 'YYYY-MM')"}
    
    result = generate_kpi_slide(dfs, month=month)
    return result


tool = {
    "name": "slides.generate_kpi",
    "description": "Generate KPI summary and narrative for a specific month.",
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

