import pandas as pd
from typing import Dict
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def calculate_runway(dfs: Dict[str, pd.DataFrame], delay_capex_days: int = 0) -> dict:
    """
    Calculate cash runway with optional CapEx delay simulation.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
        delay_capex_days: Number of days to delay CapEx payments (default: 0)
    
    Returns:
        JSON-serializable dict with runway metrics and projection
    """
    # Get current cash from latest date in fact_cash_balance_daily
    cash_df = dfs.get("fact_cash_balance_daily", pd.DataFrame())
    if cash_df.empty:
        return {
            "current_cash": 0.0,
            "monthly_burn": 0.0,
            "runway_months": 0.0,
            "projection": []
        }
    
    # Convert date column if it's a string
    if cash_df['date'].dtype == 'object':
        cash_df['date'] = pd.to_datetime(cash_df['date'])
    
    latest_date = cash_df['date'].max()
    # Sum ending_cash across all bank accounts for the latest date
    current_cash = float(cash_df[cash_df['date'] == latest_date]['ending_cash'].sum())
    
    # Calculate trailing 3-month burn
    # Get last 3 months of data
    three_months_ago = latest_date - relativedelta(months=3)
    
    # Aggregate opex from fact_gl_actuals_monthly (filter for Opex accounts)
    gl_df = dfs.get("fact_gl_actuals_monthly", pd.DataFrame())
    dim_account_df = dfs.get("dim_account", pd.DataFrame())
    
    monthly_burn = 0.0
    
    if not gl_df.empty and not dim_account_df.empty:
        # Filter for Opex accounts
        opex_accounts = dim_account_df[dim_account_df['account_type'] == 'Opex']['account_id'].tolist()
        
        # Filter for last 3 months
        if 'fiscal_month' in gl_df.columns:
            gl_df_filtered = gl_df[
                (gl_df['fiscal_month'] >= three_months_ago.strftime('%Y-%m')) &
                (gl_df['fiscal_month'] <= latest_date.strftime('%Y-%m')) &
                (gl_df['account_id'].isin(opex_accounts))
            ]
            if not gl_df_filtered.empty:
                opex_total = float(gl_df_filtered['amount_base'].sum())
                monthly_burn += opex_total / 3.0
    
    # Add payroll costs
    payroll_df = dfs.get("fact_payroll_runs", pd.DataFrame())
    if not payroll_df.empty:
        if payroll_df['pay_date'].dtype == 'object':
            payroll_df['pay_date'] = pd.to_datetime(payroll_df['pay_date'])
        
        payroll_last_3m = payroll_df[
            (payroll_df['pay_date'] >= three_months_ago) &
            (payroll_df['pay_date'] <= latest_date)
        ]
        if not payroll_last_3m.empty:
            payroll_total = float(payroll_last_3m['gross_pay'].sum() + 
                                 payroll_last_3m['taxes'].sum() + 
                                 payroll_last_3m['benefits'].sum() + 
                                 payroll_last_3m['contractor_cost'].sum())
            monthly_burn += payroll_total / 3.0
    
    # Add cloud costs
    cloud_df = dfs.get("fact_it_cloud_costs", pd.DataFrame())
    if not cloud_df.empty:
        if 'fiscal_month' in cloud_df.columns:
            cloud_last_3m = cloud_df[
                (cloud_df['fiscal_month'] >= three_months_ago.strftime('%Y-%m')) &
                (cloud_df['fiscal_month'] <= latest_date.strftime('%Y-%m'))
            ]
            if not cloud_last_3m.empty:
                cloud_total = float(cloud_last_3m['amount'].sum())
                monthly_burn += cloud_total / 3.0
    
    # Add marketing spend
    marketing_df = dfs.get("fact_marketing_spend_detail", pd.DataFrame())
    if not marketing_df.empty:
        if 'fiscal_month' in marketing_df.columns:
            marketing_last_3m = marketing_df[
                (marketing_df['fiscal_month'] >= three_months_ago.strftime('%Y-%m')) &
                (marketing_df['fiscal_month'] <= latest_date.strftime('%Y-%m'))
            ]
            if not marketing_last_3m.empty:
                marketing_total = float(marketing_last_3m['amount'].sum())
                monthly_burn += marketing_total / 3.0
    
    if monthly_burn == 0:
        return {
            "current_cash": current_cash,
            "monthly_burn": 0.0,
            "runway_months": float('inf') if current_cash > 0 else 0.0,
            "projection": []
        }
    
    # Handle CapEx schedule with delay
    capex_df = dfs.get("fact_capex_schedule", pd.DataFrame()).copy()
    if not capex_df.empty and delay_capex_days > 0:
        if 'planned_month' in capex_df.columns:
            # Convert planned_month to datetime and add delay
            capex_df['planned_month_dt'] = pd.to_datetime(capex_df['planned_month'] + '-01')
            capex_df['planned_month_dt'] = capex_df['planned_month_dt'] + timedelta(days=delay_capex_days)
            capex_df['planned_month'] = capex_df['planned_month_dt'].dt.strftime('%Y-%m')
    
    # Build monthly projection
    projection = []
    cash = current_cash
    # Start projection from the next month
    current_month = (latest_date.replace(day=1) + relativedelta(months=1))
    runway_months = 0.0
    
    # Get CapEx by month
    capex_by_month = {}
    if not capex_df.empty:
        for _, row in capex_df.iterrows():
            month = row['planned_month']
            amount = float(row['planned_amount'])
            if month not in capex_by_month:
                capex_by_month[month] = 0.0
            capex_by_month[month] += amount
    
    # Project forward until cash runs out (max 60 months)
    for i in range(60):
        month_str = current_month.strftime('%Y-%m')
        capex_for_month = capex_by_month.get(month_str, 0.0)
        total_outflow = monthly_burn + capex_for_month
        
        cash -= total_outflow
        runway_months = i + 1
        
        projection.append({
            "month": month_str,
            "cash": round(cash, 2),
            "burn": round(monthly_burn, 2),
            "capex": round(capex_for_month, 2),
            "total_outflow": round(total_outflow, 2)
        })
        
        if cash <= 0:
            break
        
        current_month = current_month + relativedelta(months=1)
    
    return {
        "current_cash": round(current_cash, 2),
        "monthly_burn": round(monthly_burn, 2),
        "runway_months": round(runway_months, 2),
        "projection": projection
    }

