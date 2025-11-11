import pandas as pd
import numpy as np
from typing import Dict


def burn_by_function(dfs: Dict[str, pd.DataFrame]) -> dict:
    """
    Calculate monthly burn rate by function/cost center.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
    
    Returns:
        JSON-serializable dict with burn by function
    """
    # Load required tables
    gl_df = dfs.get("fact_gl_actuals_monthly", pd.DataFrame()).copy()
    dim_org_df = dfs.get("dim_org", pd.DataFrame())
    dim_account_df = dfs.get("dim_account", pd.DataFrame())
    
    if gl_df.empty:
        return {"functions": []}
    
    # Filter for Opex accounts
    if not dim_account_df.empty:
        opex_accounts = dim_account_df[dim_account_df['account_type'] == 'Opex']['account_id'].tolist()
        gl_df = gl_df[gl_df['account_id'].isin(opex_accounts)]
    
    # Join with dim_org to get function
    if not dim_org_df.empty:
        gl_df = gl_df.merge(
            dim_org_df[['dept_id', 'function', 'dept_name', 'cost_center']],
            on='dept_id',
            how='left'
        )
    else:
        gl_df['function'] = 'Unknown'
        gl_df['dept_name'] = ''
        gl_df['cost_center'] = ''
    
    # Aggregate by function and month
    burn_by_function = gl_df.groupby(['function', 'fiscal_month'], as_index=False)['amount_base'].sum()
    
    # Get total by function across all months
    function_totals = burn_by_function.groupby('function', as_index=False)['amount_base'].sum()
    function_totals.rename(columns={'amount_base': 'total_burn'}, inplace=True)
    
    # Get monthly average
    monthly_counts = burn_by_function.groupby('function', as_index=False)['fiscal_month'].count()
    monthly_counts.rename(columns={'fiscal_month': 'month_count'}, inplace=True)
    
    function_summary = function_totals.merge(monthly_counts, on='function')
    function_summary['avg_monthly_burn'] = function_summary['total_burn'] / function_summary['month_count']
    
    # Sort by total burn descending
    function_summary = function_summary.sort_values('total_burn', ascending=False)
    
    # Convert to list of dicts
    functions = function_summary.to_dict('records')
    
    # Convert numpy types to native Python types
    for func in functions:
        for key, value in func.items():
            if pd.isna(value):
                func[key] = None
            elif isinstance(value, (np.integer, int)):
                func[key] = int(value)
            elif isinstance(value, (np.floating, float)):
                func[key] = float(value)
            else:
                func[key] = str(value)
    
    return {"functions": functions}

