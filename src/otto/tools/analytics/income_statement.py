"""
Income Statement Analysis from Accounting Data
"""

import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime


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


def income_statement(dfs: Dict[str, pd.DataFrame], period: str = None) -> dict:
    """
    Generate income statement from accounting data.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
        period: Optional period filter (e.g., '2024-01' for January 2024, or None for all periods)
    
    Returns:
        JSON-serializable dict with income statement line items, chart data, summary statistics, and human-readable summary
    """
    # Get accounting data
    accounting_df = dfs.get("coqley_account_data", pd.DataFrame()).copy()
    
    if accounting_df.empty:
        return {
            "income_statement": {
                "revenue": [],
                "cogs": [],
                "operating_expenses": [],
                "other": []
            },
            "totals": {
                "total_revenue": 0.0,
                "total_cogs": 0.0,
                "gross_profit": 0.0,
                "total_operating_expenses": 0.0,
                "operating_income": 0.0,
                "other_income_expense": 0.0,
                "net_income": 0.0,
                "currency": "USD"
            },
            "chart_data": {
                "income_statement": {"categories": [], "amounts": []},
                "revenue_expenses": {"categories": [], "revenue": [], "expenses": []}
            },
            "summary": {
                "period": period or "All Periods",
                "total_revenue": 0.0,
                "total_expenses": 0.0,
                "net_income": 0.0,
                "gross_margin_percent": 0.0,
                "operating_margin_percent": 0.0,
                "net_margin_percent": 0.0,
                "currency": "USD"
            },
            "summary_text": "No accounting data available."
        }
    
    # Filter by period if specified
    if period:
        accounting_df['Month'] = pd.to_datetime(accounting_df['date'], errors='coerce').dt.strftime('%Y-%m')
        accounting_df = accounting_df[accounting_df['Month'] == period]
    
    # Categorize accounts
    accounting_df['category'] = accounting_df['hisab_name'].apply(categorize_account)
    
    # Calculate revenue (from credits - d_dollar)
    revenue_df = accounting_df[accounting_df['d_dollar'] > 0].copy()
    revenue_by_account = revenue_df.groupby(['hisab_name', 'category']).agg({
        'd_dollar': 'sum'
    }).reset_index()
    
    # Calculate expenses (from debits - m_dollar)
    expense_df = accounting_df[accounting_df['m_dollar'] > 0].copy()
    expense_by_account = expense_df.groupby(['hisab_name', 'category']).agg({
        'm_dollar': 'sum'
    }).reset_index()
    
    # Build income statement line items
    revenue_items = []
    cogs_items = []
    operating_expense_items = []
    other_items = []
    
    # Revenue items
    revenue_accounts = revenue_by_account[revenue_by_account['category'] == 'Revenue']
    for _, row in revenue_accounts.iterrows():
        revenue_items.append({
            "account_name": str(row['hisab_name']),
            "amount": round(float(row['d_dollar']), 2)
        })
    
    # COGS items
    cogs_accounts = expense_by_account[expense_by_account['category'] == 'COGS']
    for _, row in cogs_accounts.iterrows():
        cogs_items.append({
            "account_name": str(row['hisab_name']),
            "amount": round(float(row['m_dollar']), 2)
        })
    
    # Operating expense items
    opex_accounts = expense_by_account[expense_by_account['category'] == 'Operating Expense']
    for _, row in opex_accounts.iterrows():
        operating_expense_items.append({
            "account_name": str(row['hisab_name']),
            "amount": round(float(row['m_dollar']), 2)
        })
    
    # Other items (revenue and expenses that don't fit categories)
    other_revenue = revenue_by_account[revenue_by_account['category'] == 'Other']
    other_expenses = expense_by_account[expense_by_account['category'] == 'Other']
    
    for _, row in other_revenue.iterrows():
        other_items.append({
            "account_name": str(row['hisab_name']),
            "amount": round(float(row['d_dollar']), 2),
            "type": "income"
        })
    
    for _, row in other_expenses.iterrows():
        other_items.append({
            "account_name": str(row['hisab_name']),
            "amount": round(float(row['m_dollar']), 2),
            "type": "expense"
        })
    
    # Calculate totals
    total_revenue = revenue_by_account['d_dollar'].sum() + other_revenue['d_dollar'].sum() if not other_revenue.empty else revenue_by_account['d_dollar'].sum()
    total_cogs = cogs_accounts['m_dollar'].sum() if not cogs_accounts.empty else 0.0
    gross_profit = total_revenue - total_cogs
    total_operating_expenses = opex_accounts['m_dollar'].sum() if not opex_accounts.empty else 0.0
    operating_income = gross_profit - total_operating_expenses
    other_income_expense = (other_revenue['d_dollar'].sum() if not other_revenue.empty else 0.0) - (other_expenses['m_dollar'].sum() if not other_expenses.empty else 0.0)
    net_income = operating_income + other_income_expense
    
    # Calculate margins
    gross_margin_percent = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0.0
    operating_margin_percent = (operating_income / total_revenue * 100) if total_revenue > 0 else 0.0
    net_margin_percent = (net_income / total_revenue * 100) if total_revenue > 0 else 0.0
    
    # Prepare chart data
    chart_data = {
        "income_statement": {
            "categories": ["Revenue", "COGS", "Gross Profit", "Operating Expenses", "Operating Income", "Other", "Net Income"],
            "amounts": [
                round(total_revenue, 2),
                round(-total_cogs, 2),  # Negative for expenses
                round(gross_profit, 2),
                round(-total_operating_expenses, 2),  # Negative for expenses
                round(operating_income, 2),
                round(other_income_expense, 2),
                round(net_income, 2)
            ],
            "chart_type": "bar",
            "title": "Income Statement",
            "xlabel": "Category",
            "ylabel": "Amount (USD)"
        },
        "revenue_expenses": {
            "categories": ["Total Revenue", "Total Expenses", "Net Income"],
            "revenue": [round(total_revenue, 2), 0, 0],
            "expenses": [0, round(total_cogs + total_operating_expenses, 2), 0],
            "net_income": [0, 0, round(net_income, 2)],
            "chart_type": "bar",
            "title": "Revenue vs Expenses",
            "xlabel": "Category",
            "ylabel": "Amount (USD)",
            "legend": ["Revenue", "Expenses", "Net Income"]
        }
    }
    
    # Generate human-readable summary
    summary_parts = []
    if period:
        summary_parts.append(f"Income statement for period {period}.")
    else:
        summary_parts.append("Income statement for all periods.")
    
    summary_parts.append(f"Total revenue: ${total_revenue:,.2f}.")
    summary_parts.append(f"Cost of goods sold: ${total_cogs:,.2f}.")
    summary_parts.append(f"Gross profit: ${gross_profit:,.2f} ({gross_margin_percent:.1f}% margin).")
    summary_parts.append(f"Operating expenses: ${total_operating_expenses:,.2f}.")
    summary_parts.append(f"Operating income: ${operating_income:,.2f} ({operating_margin_percent:.1f}% margin).")
    
    if abs(other_income_expense) > 0.01:
        summary_parts.append(f"Other income/(expense): ${other_income_expense:,.2f}.")
    
    summary_parts.append(f"Net income: ${net_income:,.2f} ({net_margin_percent:.1f}% margin).")
    
    summary_text = " ".join(summary_parts)
    
    return {
        "income_statement": {
            "revenue": sorted(revenue_items, key=lambda x: x['amount'], reverse=True),
            "cogs": sorted(cogs_items, key=lambda x: x['amount'], reverse=True),
            "operating_expenses": sorted(operating_expense_items, key=lambda x: x['amount'], reverse=True),
            "other": sorted(other_items, key=lambda x: x['amount'], reverse=True)
        },
        "totals": {
            "total_revenue": round(total_revenue, 2),
            "total_cogs": round(total_cogs, 2),
            "gross_profit": round(gross_profit, 2),
            "total_operating_expenses": round(total_operating_expenses, 2),
            "operating_income": round(operating_income, 2),
            "other_income_expense": round(other_income_expense, 2),
            "net_income": round(net_income, 2),
            "currency": "USD"
        },
        "chart_data": chart_data,
        "summary": {
            "period": period or "All Periods",
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_cogs + total_operating_expenses, 2),
            "net_income": round(net_income, 2),
            "gross_margin_percent": round(gross_margin_percent, 2),
            "operating_margin_percent": round(operating_margin_percent, 2),
            "net_margin_percent": round(net_margin_percent, 2),
            "currency": "USD"
        },
        "summary_text": summary_text
    }

