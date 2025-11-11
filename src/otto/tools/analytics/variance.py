import pandas as pd
import numpy as np
from typing import Dict


def variance_report(dfs: Dict[str, pd.DataFrame], fiscal_quarter: str, budget_version: str) -> dict:
    """
    Generate actual vs budget variance report by fiscal quarter and budget version.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
        fiscal_quarter: Fiscal quarter (e.g., "Q1", "Q2")
        budget_version: Budget version (e.g., "BUDGET_2024")
    
    Returns:
        JSON-serializable dict with variance rows
    """
    # Load required tables
    actuals_df = dfs.get("fact_gl_actuals_monthly", pd.DataFrame()).copy()
    budget_df = dfs.get("fact_budget_monthly", pd.DataFrame()).copy()
    dim_org_df = dfs.get("dim_org", pd.DataFrame())
    dim_account_df = dfs.get("dim_account", pd.DataFrame())
    dim_time_df = dfs.get("dim_time", pd.DataFrame())
    
    if actuals_df.empty or budget_df.empty:
        return {"rows": []}
    
    # Map fiscal months to quarters using dim_time
    month_to_quarter = {}
    if not dim_time_df.empty:
        for _, row in dim_time_df.iterrows():
            month = row['fiscal_month']
            quarter = row['fiscal_quarter']
            if month not in month_to_quarter:
                month_to_quarter[month] = quarter
    
    # Filter budget by version
    budget_df = budget_df[budget_df['version'] == budget_version]
    
    # Filter by quarter
    if month_to_quarter:
        # Filter actuals by quarter
        actuals_df['fiscal_quarter'] = actuals_df['fiscal_month'].map(month_to_quarter)
        actuals_df = actuals_df[actuals_df['fiscal_quarter'] == fiscal_quarter]
        
        # Filter budget by quarter
        budget_df['fiscal_quarter'] = budget_df['fiscal_month'].map(month_to_quarter)
        budget_df = budget_df[budget_df['fiscal_quarter'] == fiscal_quarter]
    else:
        # Fallback: assume quarter format in fiscal_month or use first char
        # This is a simple fallback - in practice, you'd want proper quarter mapping
        return {"rows": []}
    
    # Aggregate actuals by dept_id and account_id
    actuals_agg = actuals_df.groupby(['dept_id', 'account_id'], as_index=False)['amount_base'].sum()
    actuals_agg.rename(columns={'amount_base': 'actual'}, inplace=True)
    
    # Aggregate budget by dept_id and account_id
    budget_agg = budget_df.groupby(['dept_id', 'account_id'], as_index=False)['amount_base'].sum()
    budget_agg.rename(columns={'amount_base': 'budget'}, inplace=True)
    
    # Merge actuals and budget
    variance_df = actuals_agg.merge(budget_agg, on=['dept_id', 'account_id'], how='outer')
    variance_df.fillna(0, inplace=True)
    
    # Join with dim_org
    if not dim_org_df.empty:
        variance_df = variance_df.merge(
            dim_org_df[['dept_id', 'dept_name', 'function', 'cost_center']],
            on='dept_id',
            how='left'
        )
    else:
        variance_df['dept_name'] = ''
        variance_df['function'] = ''
        variance_df['cost_center'] = ''
    
    # Join with dim_account
    if not dim_account_df.empty:
        variance_df = variance_df.merge(
            dim_account_df[['account_id', 'account_name', 'account_type', 'rollup_group']],
            on='account_id',
            how='left'
        )
    else:
        variance_df['account_name'] = ''
        variance_df['account_type'] = ''
        variance_df['rollup_group'] = ''
    
    # Calculate variance
    variance_df['variance'] = variance_df['actual'] - variance_df['budget']
    variance_df['variance_pct'] = (variance_df['variance'] / variance_df['budget'].replace(0, 1)) * 100
    variance_df['variance_pct'] = variance_df['variance_pct'].replace([float('inf'), float('-inf')], 0)
    
    # Fill NaN values
    variance_df.fillna('', inplace=True)
    
    # Convert to list of dicts
    rows = variance_df.to_dict('records')
    
    # Convert numpy types to native Python types for JSON serialization
    for row in rows:
        for key, value in row.items():
            if pd.isna(value):
                row[key] = None
            elif isinstance(value, pd.Timestamp):
                row[key] = str(value)
            elif isinstance(value, (np.integer, int)):
                row[key] = int(value)
            elif isinstance(value, (np.floating, float)):
                row[key] = float(value)
            elif value == '':
                # Keep empty strings as is
                pass
            else:
                row[key] = str(value)
    
    return {"rows": rows}

