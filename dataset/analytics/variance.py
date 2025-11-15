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
        return {
            "rows": [],
            "summary": {
                "fiscal_quarter": fiscal_quarter,
                "budget_version": budget_version,
                "total_rows": 0,
                "total_actual": 0.0,
                "total_budget": 0.0,
                "total_variance": 0.0,
                "currency": "USD"
            },
            "summary_text": f"No data available for quarter {fiscal_quarter} and budget version {budget_version}."
        }
    
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
        return {
            "rows": [],
            "summary": {
                "fiscal_quarter": fiscal_quarter,
                "budget_version": budget_version,
                "total_rows": 0,
                "total_actual": 0.0,
                "total_budget": 0.0,
                "total_variance": 0.0,
                "currency": "USD"
            },
            "summary_text": f"Could not map months to quarters. No variance report generated."
        }
    
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
                row[key] = round(float(value), 2)
            elif value == '':
                # Keep empty strings as is
                pass
            else:
                row[key] = str(value)
    
    # Calculate summary statistics
    total_actual = sum(r.get('actual', 0) for r in rows)
    total_budget = sum(r.get('budget', 0) for r in rows)
    total_variance = total_actual - total_budget
    total_variance_pct = (total_variance / total_budget * 100) if total_budget != 0 else 0.0
    
    # Count variances
    favorable_count = sum(1 for r in rows if r.get('variance', 0) < 0)
    unfavorable_count = sum(1 for r in rows if r.get('variance', 0) > 0)
    on_budget_count = sum(1 for r in rows if r.get('variance', 0) == 0)
    
    # Find largest variances
    rows_sorted = sorted(rows, key=lambda x: abs(x.get('variance', 0)), reverse=True)
    largest_favorable = next((r for r in rows_sorted if r.get('variance', 0) < 0), None)
    largest_unfavorable = next((r for r in rows_sorted if r.get('variance', 0) > 0), None)
    
    # Generate human-readable summary
    summary_parts = []
    summary_parts.append(f"Variance report for {fiscal_quarter} using budget version {budget_version}.")
    summary_parts.append(f"Total actual: ${total_actual:,.2f}, Total budget: ${total_budget:,.2f}.")
    summary_parts.append(f"Total variance: ${total_variance:,.2f} ({total_variance_pct:+.1f}%).")
    
    if total_variance < 0:
        summary_parts.append("Overall: Under budget (favorable).")
    elif total_variance > 0:
        summary_parts.append("Overall: Over budget (unfavorable).")
    else:
        summary_parts.append("Overall: On budget.")
    
    summary_parts.append(
        f"Breakdown: {favorable_count} favorable variances, "
        f"{unfavorable_count} unfavorable variances, "
        f"{on_budget_count} on budget."
    )
    
    if largest_unfavorable:
        summary_parts.append(
            f"Largest unfavorable variance: {largest_unfavorable.get('account_name', 'N/A')} "
            f"({largest_unfavorable.get('function', 'N/A')}) "
            f"at ${largest_unfavorable.get('variance', 0):,.2f} "
            f"({largest_unfavorable.get('variance_pct', 0):+.1f}%)."
        )
    
    if largest_favorable:
        summary_parts.append(
            f"Largest favorable variance: {largest_favorable.get('account_name', 'N/A')} "
            f"({largest_favorable.get('function', 'N/A')}) "
            f"at ${largest_favorable.get('variance', 0):,.2f} "
            f"({largest_favorable.get('variance_pct', 0):+.1f}%)."
        )
    
    summary_text = " ".join(summary_parts)
    
    return {
        "rows": rows,
        "summary": {
            "fiscal_quarter": fiscal_quarter,
            "budget_version": budget_version,
            "total_rows": len(rows),
            "total_actual": round(total_actual, 2),
            "total_budget": round(total_budget, 2),
            "total_variance": round(total_variance, 2),
            "total_variance_pct": round(total_variance_pct, 2),
            "favorable_count": favorable_count,
            "unfavorable_count": unfavorable_count,
            "on_budget_count": on_budget_count,
            "currency": "USD"
        },
        "summary_text": summary_text
    }

