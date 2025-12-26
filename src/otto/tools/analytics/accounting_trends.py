"""
Accounting Monthly Revenue/Expense Trends Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime


def accounting_monthly_trends(dfs: Dict[str, pd.DataFrame]) -> dict:
    """
    Calculate monthly revenue/expense trends from accounting data.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
    
    Returns:
        JSON-serializable dict with monthly trends, chart data, summary statistics, and human-readable summary
    """
    # Get accounting data
    accounting_df = dfs.get("coqley_account_data", pd.DataFrame()).copy()
    
    if accounting_df.empty:
        return {
            "monthly_trends": [],
            "chart_data": {
                "revenue_expenses": {"months": [], "revenue": [], "expenses": []},
                "net_income": {"months": [], "net_income": []}
            },
            "summary": {
                "total_revenue": 0.0,
                "total_expenses": 0.0,
                "net_income": 0.0,
                "number_of_months": 0,
                "currency": "USD"
            },
            "summary_text": "No accounting data available."
        }
    
    # Extract month from date column
    accounting_df['Month'] = pd.to_datetime(accounting_df['date'], errors='coerce').dt.to_period('M')
    accounting_df['Month_Name'] = pd.to_datetime(accounting_df['date'], errors='coerce').dt.strftime('%Y-%m')
    
    # Filter out invalid dates
    accounting_df = accounting_df[accounting_df['Month_Name'].notna()]
    
    # Calculate monthly totals
    monthly_summary = accounting_df.groupby('Month_Name').agg({
        'm_dollar': 'sum',  # Debits (Expenses)
        'd_dollar': 'sum',  # Credits (Revenue/Income)
    }).fillna(0)
    
    # Calculate net income
    monthly_summary['Net Income USD'] = monthly_summary['d_dollar'] - monthly_summary['m_dollar']
    
    # Sort by month
    monthly_summary = monthly_summary.sort_index()
    
    # Convert to list of dicts
    trends = []
    for month, row in monthly_summary.iterrows():
        trends.append({
            "month": str(month),
            "revenue": round(float(row['d_dollar']), 2),
            "expenses": round(float(row['m_dollar']), 2),
            "net_income": round(float(row['Net Income USD']), 2)
        })
    
    # Prepare chart data for LLM to recreate charts
    chart_data = {
        "revenue_expenses": {
            "months": [t["month"] for t in trends],
            "revenue": [t["revenue"] for t in trends],
            "expenses": [t["expenses"] for t in trends],
            "chart_type": "bar",
            "title": "Monthly Revenue vs Expenses",
            "xlabel": "Month",
            "ylabel": "Amount (USD)",
            "legend": ["Revenue (Credits)", "Expenses (Debits)"]
        },
        "net_income": {
            "months": [t["month"] for t in trends],
            "net_income": [t["net_income"] for t in trends],
            "chart_type": "line",
            "title": "Monthly Net Income Trend",
            "xlabel": "Month",
            "ylabel": "Net Income (USD)",
            "marker": "o"
        }
    }
    
    # Calculate summary statistics
    total_revenue = monthly_summary['d_dollar'].sum()
    total_expenses = monthly_summary['m_dollar'].sum()
    net_income = total_revenue - total_expenses
    avg_monthly_revenue = monthly_summary['d_dollar'].mean()
    avg_monthly_expenses = monthly_summary['m_dollar'].mean()
    
    # Generate human-readable summary
    summary_parts = [f"Monthly trends analysis for {len(trends)} months."]
    summary_parts.append(f"Total revenue: ${total_revenue:,.2f}.")
    summary_parts.append(f"Total expenses: ${total_expenses:,.2f}.")
    summary_parts.append(f"Net income: ${net_income:,.2f}.")
    summary_parts.append(f"Average monthly revenue: ${avg_monthly_revenue:,.2f}.")
    summary_parts.append(f"Average monthly expenses: ${avg_monthly_expenses:,.2f}.")
    
    if trends:
        best_month = max(trends, key=lambda x: x['net_income'])
        worst_month = min(trends, key=lambda x: x['net_income'])
        highest_revenue_month = max(trends, key=lambda x: x['revenue'])
        highest_expense_month = max(trends, key=lambda x: x['expenses'])
        
        summary_parts.append(f"Best month (highest net income): {best_month['month']} with ${best_month['net_income']:,.2f}.")
        summary_parts.append(f"Worst month (lowest net income): {worst_month['month']} with ${worst_month['net_income']:,.2f}.")
        summary_parts.append(f"Highest revenue month: {highest_revenue_month['month']} with ${highest_revenue_month['revenue']:,.2f}.")
        summary_parts.append(f"Highest expense month: {highest_expense_month['month']} with ${highest_expense_month['expenses']:,.2f}.")
    
    summary_text = " ".join(summary_parts)
    
    return {
        "monthly_trends": trends,
        "chart_data": chart_data,
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "net_income": round(net_income, 2),
            "average_monthly_revenue": round(avg_monthly_revenue, 2),
            "average_monthly_expenses": round(avg_monthly_expenses, 2),
            "number_of_months": len(trends),
            "currency": "USD"
        },
        "summary_text": summary_text
    }

