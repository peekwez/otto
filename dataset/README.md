# Financial Analytics Layer

A financial analytics layer exposed via MCP (Model Context Protocol) tools for CFO data analysis.

## Architecture

```
project/
  load_data.py              # loads Aiven Postgres tables into dfs
  analytics/
      runway.py             # cash runway calculator (+ capex delay simulation)
      variance.py           # actual vs budget variance reporting
      burn.py               # burn by function / cost center analysis
      cloud_marketing.py    # cloud & marketing spend drilldown
      slides.py             # KPI summary + narrative generator
  mcp/
      runway_tool.py
      variance_tool.py
      burn_tool.py
      cloud_marketing_tool.py
      slides_tool.py
  run.py                    # local test runner to call functions manually
  README.md
```

## Design Principles

1. **load_data.py** exposes `load_all_tables() -> dict[str, pd.DataFrame]` which returns all tables from the database
2. **Analytics functions**:
   - Accept `dfs` (dict of DataFrames) as first argument
   - Contain ZERO database calls inside analytics modules
   - Return JSON-serializable dicts (no DataFrames in return)
3. **MCP tool wrappers**:
   - Import corresponding analytics functions
   - Validate arguments
   - Return values exactly as JSON dicts
   - Include a `tool` definition compatible with MCP schema

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Local Testing

Use `run.py` to test analytics functions locally:

```bash
# Calculate cash runway
python run.py runway --delay 90

# Generate variance report
python run.py variance --month 2024-03 --version BUDGET_2024

# Calculate burn by function
python run.py burn

# Cloud and marketing breakdown
python run.py cloud_marketing --month 2024-01

# Generate KPI slide
python run.py slides --month 2024-01
```

### MCP Tools

Each MCP tool can be imported and used programmatically:

```python
from mcp.runway_tool import runway_tool

result = runway_tool({"delay_capex_days": 90})
```

## Analytics Functions

### runway.py

Calculates cash runway with optional CapEx delay simulation.

**Returns:**
```json
{
  "current_cash": float,
  "monthly_burn": float,
  "runway_months": float,
  "projection": [
    {"month": "2024-04", "cash": 12345, "burn": 50000, "capex": 20000, "total_outflow": 70000},
    ...
  ]
}
```

### variance.py

Generates actual vs budget variance report by fiscal quarter and budget version.

**Returns:**
```json
{
  "rows": [
    {
      "dept_id": int,
      "account_id": int,
      "actual": float,
      "budget": float,
      "variance": float,
      "variance_pct": float,
      "dept_name": str,
      "function": str,
      "account_name": str,
      "rollup_group": str
    },
    ...
  ]
}
```

### burn.py

Calculates monthly burn rate by function/cost center.

**Returns:**
```json
{
  "functions": [
    {
      "function": str,
      "total_burn": float,
      "month_count": int,
      "avg_monthly_burn": float
    },
    ...
  ]
}
```

### cloud_marketing.py

Generates cloud and marketing spend breakdown for a specific month.

**Returns:**
```json
{
  "cloud_costs": [
    {"provider": str, "service": str, "env": str, "amount": float},
    ...
  ],
  "marketing_spend": [
    {"channel": str, "campaign_id": str, "amount": float},
    ...
  ],
  "total_cloud": float,
  "total_marketing": float
}
```

### slides.py

Generates KPI summary and narrative for a specific month.

**Returns:**
```json
{
  "month": str,
  "kpis": [
    {
      "kpi_id": int,
      "name": str,
      "value": float,
      "target_value": float,
      "status": str
    },
    ...
  ],
  "narrative": str,
  "key_metrics": {
    "KPI_name": {
      "value": float,
      "target": float,
      "status": str
    }
  }
}
```

## Database Schema

The analytics layer connects to an Aiven PostgreSQL database with the following key tables:

- `fact_cash_balance_daily` - Daily cash balances
- `fact_gl_actuals_monthly` - Monthly GL actuals
- `fact_budget_monthly` - Monthly budget data
- `fact_payroll_runs` - Payroll data
- `fact_it_cloud_costs` - Cloud infrastructure costs
- `fact_marketing_spend_detail` - Marketing spend details
- `fact_capex_schedule` - Capital expenditure schedule
- `dim_org` - Organizational dimensions
- `dim_account` - Account dimensions
- `dim_time` - Time dimensions
- `kpi_monthly` - Monthly KPI values
- `metric_targets` - KPI targets
- `commentary_library` - Narrative templates

See `database_documentation_full.md` for complete schema documentation.

## Requirements

- pandas >= 2.0.0
- sqlalchemy >= 2.0.0
- psycopg2-binary >= 2.9.0
- python-dateutil >= 2.8.0

## Notes

- All return values are JSON-serializable (no DataFrames in return)
- No direct printing inside analytics code
- No BI formatting; just structured output
- No GUI charts; MCP tools return pure JSON

