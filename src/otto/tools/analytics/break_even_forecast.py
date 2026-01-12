"""
Monthly Break-Even Forecasting Analysis
Forecasts monthly break-even points for future months/years based on historical accounting data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


def categorize_account(account_name: str) -> str:
    """
    Categorize account based on name patterns.
    Returns: 'Revenue', 'COGS', 'Operating Expense', or 'Other'
    """
    name_lower = str(account_name).lower()
    
    # Revenue indicators
    revenue_keywords = ['revenue', 'income', 'sales', 'revenue', 'subscription', 'service income', 
                       'product sales', 'interest income', 'other income']
    if any(keyword in name_lower for keyword in revenue_keywords):
        return 'Revenue'
    
    # COGS indicators
    cogs_keywords = ['cogs', 'cost of goods', 'cost of sales', 'direct cost', 'production cost',
                     'material', 'inventory', 'purchase', 'wholesale']
    if any(keyword in name_lower for keyword in cogs_keywords):
        return 'COGS'
    
    # Operating expense indicators
    opex_keywords = ['marketing', 'advertising', 'sales', 'general', 'administrative', 'g&a',
                     'operating', 'rent', 'utilities', 'salary', 'payroll', 'software', 'it',
                     'consulting', 'professional', 'legal', 'insurance', 'depreciation', 'amortization']
    if any(keyword in name_lower for keyword in opex_keywords):
        return 'Operating Expense'
    
    return 'Other'


def break_even_forecast(
    dfs: Dict[str, pd.DataFrame],
    forecast_months: int = 12,
    start_date: Optional[str] = None,
    revenue_growth_rate: float = 0.0,
    expense_growth_rate: float = 0.0
) -> dict:
    """
    Forecast monthly break-even points for future months based on historical accounting data.
    
    Break-even is calculated as the point where cumulative revenue >= cumulative expenses for each month.
    
    IMPORTANT: In double-entry bookkeeping, total debits always equal total credits across ALL accounts.
    However, break-even compares REVENUE (from Revenue accounts) vs EXPENSES (from Expense/COGS accounts).
    We filter by account type to get actual business revenue vs expenses, not just all debits/credits.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
        forecast_months: Number of months to forecast into the future (default: 12)
        start_date: Start date for forecast in YYYY-MM format. If None, uses month after last data point
        revenue_growth_rate: Monthly growth rate for revenue (e.g., 0.05 = 5% monthly growth, default: 0.0)
        expense_growth_rate: Monthly growth rate for expenses (e.g., 0.02 = 2% monthly growth, default: 0.0)
    
    Returns:
        JSON-serializable dict with monthly break-even forecasts, chart data, summary statistics, and human-readable summary
    """
    # Get accounting data
    accounting_df = dfs.get("coqley_account_data", pd.DataFrame()).copy()
    
    if accounting_df.empty:
        return {
            "historical_monthly": [],
            "forecast_monthly": [],
            "break_even_months": [],
            "chart_data": {
                "monthly_revenue_expenses": {"months": [], "revenue": [], "expenses": [], "net": []},
                "cumulative_break_even": {"months": [], "cumulative_revenue": [], "cumulative_expenses": [], "break_even_line": []}
            },
            "summary": {
                "historical_avg_monthly_revenue": 0.0,
                "historical_avg_monthly_expenses": 0.0,
                "forecast_period_months": 0,
                "break_even_months_count": 0,
                "currency": "USD"
            },
            "summary_text": "No accounting data available."
        }
    
    # Ensure date column is datetime
    accounting_df['date'] = pd.to_datetime(accounting_df['date'], errors='coerce')
    accounting_df = accounting_df[accounting_df['date'].notna()]
    
    if accounting_df.empty:
        return {
            "historical_monthly": [],
            "forecast_monthly": [],
            "break_even_months": [],
            "chart_data": {},
            "summary": {},
            "summary_text": "No valid date data available."
        }
    
    # CRITICAL: Categorize accounts to properly identify revenue vs expenses
    # In double-entry bookkeeping, we can't just sum all credits/debits
    # We need to filter by account type
    accounting_df['category'] = accounting_df['hisab_name'].apply(categorize_account)
    
    # Add year-month period for monthly aggregation
    accounting_df['year_month'] = accounting_df['date'].dt.to_period('M')
    
    # Calculate monthly revenue from Revenue accounts (credits in revenue accounts)
    # Revenue accounts increase with credits (d_dollar)
    revenue_accounts = accounting_df[accounting_df['category'] == 'Revenue'].copy()
    monthly_revenue = revenue_accounts.groupby('year_month').agg({
        'd_dollar': 'sum'  # Credits in revenue accounts = revenue
    }).fillna(0)
    monthly_revenue.columns = ['revenue']
    
    # Calculate monthly expenses from COGS and Operating Expense accounts (debits in expense accounts)
    # Expense accounts increase with debits (m_dollar)
    expense_accounts = accounting_df[accounting_df['category'].isin(['COGS', 'Operating Expense'])].copy()
    monthly_expenses = expense_accounts.groupby('year_month').agg({
        'm_dollar': 'sum'  # Debits in expense accounts = expenses
    }).fillna(0)
    monthly_expenses.columns = ['expenses']
    
    # Combine revenue and expenses
    monthly_summary = pd.DataFrame(index=pd.period_range(
        start=accounting_df['year_month'].min(),
        end=accounting_df['year_month'].max(),
        freq='M'
    ))
    monthly_summary = monthly_summary.join(monthly_revenue, how='left').join(monthly_expenses, how='left')
    monthly_summary = monthly_summary.fillna(0)
    
    monthly_summary['net'] = monthly_summary['revenue'] - monthly_summary['expenses']
    
    # Sort by period
    monthly_summary = monthly_summary.sort_index()
    
    # Calculate historical averages
    avg_monthly_revenue = monthly_summary['revenue'].mean()
    avg_monthly_expenses = monthly_summary['expenses'].mean()
    
    # Calculate growth trends from historical data if available
    if len(monthly_summary) > 1:
        # Use last 3 months for trend if available
        recent_months = monthly_summary.tail(3)
        if len(recent_months) > 1:
            revenue_trend = (recent_months['revenue'].iloc[-1] / recent_months['revenue'].iloc[0] - 1) / len(recent_months)
            expense_trend = (recent_months['expenses'].iloc[-1] / recent_months['expenses'].iloc[0] - 1) / len(recent_months)
            # If user didn't specify growth rates, use calculated trends
            if revenue_growth_rate == 0.0:
                revenue_growth_rate = max(revenue_trend, 0)  # Only use positive trends
            if expense_growth_rate == 0.0:
                expense_growth_rate = max(expense_trend, 0)
    
    # Determine forecast start period
    last_period = monthly_summary.index.max()
    if start_date:
        # Parse start_date as YYYY-MM and convert to period
        forecast_start_period = pd.Period(start_date, freq='M')
    else:
        # Start from the month after the last data point
        forecast_start_period = last_period + 1
    
    # Generate forecast periods
    forecast_end_period = forecast_start_period + forecast_months - 1
    forecast_periods = pd.period_range(start=forecast_start_period, end=forecast_end_period, freq='M')
    
    # Calculate base monthly amounts (use recent average or last month)
    if len(monthly_summary) > 0:
        base_monthly_revenue = monthly_summary['revenue'].iloc[-1] if monthly_summary['revenue'].iloc[-1] > 0 else avg_monthly_revenue
        base_monthly_expenses = monthly_summary['expenses'].iloc[-1] if monthly_summary['expenses'].iloc[-1] > 0 else avg_monthly_expenses
    else:
        base_monthly_revenue = avg_monthly_revenue
        base_monthly_expenses = avg_monthly_expenses
    
    # Generate forecast
    forecast_data = []
    cumulative_revenue = 0.0
    cumulative_expenses = 0.0
    break_even_months = []
    
    for i, period in enumerate(forecast_periods):
        # Calculate growth multiplier
        months_from_start = i
        month_multiplier_revenue = (1 + revenue_growth_rate) ** months_from_start
        month_multiplier_expenses = (1 + expense_growth_rate) ** months_from_start
        
        # Calculate monthly amounts with growth
        monthly_revenue_amt = base_monthly_revenue * month_multiplier_revenue
        monthly_expenses_amt = base_monthly_expenses * month_multiplier_expenses
        
        # Update cumulative
        cumulative_revenue += monthly_revenue_amt
        cumulative_expenses += monthly_expenses_amt
        
        net = monthly_revenue_amt - monthly_expenses_amt
        cumulative_net = cumulative_revenue - cumulative_expenses
        
        # Check if this is a break-even month (cumulative revenue >= cumulative expenses)
        is_break_even = bool(cumulative_revenue >= cumulative_expenses)
        
        forecast_data.append({
            "month": str(period),
            "revenue": round(monthly_revenue_amt, 2),
            "expenses": round(monthly_expenses_amt, 2),
            "net": round(net, 2),
            "cumulative_revenue": round(cumulative_revenue, 2),
            "cumulative_expenses": round(cumulative_expenses, 2),
            "cumulative_net": round(cumulative_net, 2),
            "is_break_even": is_break_even
        })
        
        if is_break_even:
            break_even_months.append({
                "month": str(period),
                "cumulative_revenue": round(cumulative_revenue, 2),
                "cumulative_expenses": round(cumulative_expenses, 2),
                "cumulative_net": round(cumulative_net, 2)
            })
    
    # Prepare historical monthly data
    historical_monthly = []
    hist_cumulative_revenue = 0.0
    hist_cumulative_expenses = 0.0
    
    for period, row in monthly_summary.iterrows():
        hist_cumulative_revenue += row['revenue']
        hist_cumulative_expenses += row['expenses']
        hist_net = row['net']
        hist_cumulative_net = hist_cumulative_revenue - hist_cumulative_expenses
        
        historical_monthly.append({
            "month": str(period),
            "revenue": round(float(row['revenue']), 2),
            "expenses": round(float(row['expenses']), 2),
            "net": round(float(hist_net), 2),
            "cumulative_revenue": round(hist_cumulative_revenue, 2),
            "cumulative_expenses": round(hist_cumulative_expenses, 2),
            "cumulative_net": round(hist_cumulative_net, 2),
            "is_break_even": bool(hist_cumulative_revenue >= hist_cumulative_expenses)
        })
    
    # Prepare chart data
    all_months = [h["month"] for h in historical_monthly[-12:]] + [f["month"] for f in forecast_data]  # Last 12 months + forecast
    all_revenue = [h["revenue"] for h in historical_monthly[-12:]] + [f["revenue"] for f in forecast_data]
    all_expenses = [h["expenses"] for h in historical_monthly[-12:]] + [f["expenses"] for f in forecast_data]
    all_net = [h["net"] for h in historical_monthly[-12:]] + [f["net"] for f in forecast_data]
    
    cumulative_revenue_forecast = [h["cumulative_revenue"] for h in historical_monthly[-12:]] + [f["cumulative_revenue"] for f in forecast_data]
    cumulative_expenses_forecast = [h["cumulative_expenses"] for h in historical_monthly[-12:]] + [f["cumulative_expenses"] for f in forecast_data]
    # Break-even line (where cumulative revenue = cumulative expenses)
    break_even_line = [min(rev, exp) for rev, exp in zip(cumulative_revenue_forecast, cumulative_expenses_forecast)]
    
    chart_data = {
        "monthly_revenue_expenses": {
            "months": all_months,
            "revenue": all_revenue,
            "expenses": all_expenses,
            "net": all_net,
            "chart_type": "line",
            "title": "Monthly Revenue vs Expenses (Historical + Forecast)",
            "xlabel": "Month",
            "ylabel": "Amount (USD)",
            "legend": ["Revenue", "Expenses", "Net"]
        },
        "cumulative_break_even": {
            "months": all_months,
            "cumulative_revenue": cumulative_revenue_forecast,
            "cumulative_expenses": cumulative_expenses_forecast,
            "break_even_line": break_even_line,
            "chart_type": "line",
            "title": "Cumulative Revenue vs Expenses (Break-Even Analysis)",
            "xlabel": "Month",
            "ylabel": "Cumulative Amount (USD)",
            "legend": ["Cumulative Revenue", "Cumulative Expenses", "Break-Even Line"]
        }
    }
    
    # Calculate summary statistics
    forecast_period_months = len(forecast_data)
    break_even_months_count = len(break_even_months)
    break_even_percentage = (break_even_months_count / forecast_period_months * 100) if forecast_period_months > 0 else 0.0
    
    # Find first break-even month in forecast
    first_break_even = break_even_months[0] if break_even_months else None
    
    # Generate human-readable summary
    summary_parts = [f"Monthly break-even forecast for {forecast_months} months."]
    summary_parts.append(f"Historical average monthly revenue: ${avg_monthly_revenue:,.2f}.")
    summary_parts.append(f"Historical average monthly expenses: ${avg_monthly_expenses:,.2f}.")
    summary_parts.append(f"Forecast base monthly revenue: ${base_monthly_revenue:,.2f}.")
    summary_parts.append(f"Forecast base monthly expenses: ${base_monthly_expenses:,.2f}.")
    
    if revenue_growth_rate != 0.0:
        summary_parts.append(f"Revenue growth rate: {revenue_growth_rate*100:.2f}% per month.")
    if expense_growth_rate != 0.0:
        summary_parts.append(f"Expense growth rate: {expense_growth_rate*100:.2f}% per month.")
    
    summary_parts.append(f"Break-even months in forecast period: {break_even_months_count} ({break_even_percentage:.1f}% of months).")
    
    if first_break_even:
        summary_parts.append(f"First break-even month: {first_break_even['month']} with cumulative net of ${first_break_even['cumulative_net']:,.2f}.")
    else:
        summary_parts.append("No break-even months in forecast period (expenses exceed revenue throughout).")
    
    if forecast_data:
        final_month = forecast_data[-1]
        summary_parts.append(
            f"Final month forecast ({final_month['month']}): "
            f"Monthly revenue ${final_month['revenue']:,.2f}, "
            f"Monthly expenses ${final_month['expenses']:,.2f}, "
            f"Cumulative net ${final_month['cumulative_net']:,.2f}."
        )
    
    summary_text = " ".join(summary_parts)
    
    return {
        "historical_monthly": historical_monthly[-12:],  # Last 12 months for context
        "forecast_monthly": forecast_data,
        "break_even_months": break_even_months,
        "chart_data": chart_data,
        "summary": {
            "historical_avg_monthly_revenue": round(avg_monthly_revenue, 2),
            "historical_avg_monthly_expenses": round(avg_monthly_expenses, 2),
            "forecast_base_monthly_revenue": round(base_monthly_revenue, 2),
            "forecast_base_monthly_expenses": round(base_monthly_expenses, 2),
            "revenue_growth_rate": round(revenue_growth_rate * 100, 2),
            "expense_growth_rate": round(expense_growth_rate * 100, 2),
            "forecast_period_months": forecast_period_months,
            "break_even_months_count": break_even_months_count,
            "break_even_percentage": round(break_even_percentage, 2),
            "first_break_even_month": first_break_even['month'] if first_break_even else None,
            "forecast_start_month": str(forecast_start_period),
            "forecast_end_month": str(forecast_end_period),
            "currency": "USD"
        },
        "summary_text": summary_text
    }

