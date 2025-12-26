"""
Accounting Top Accounts by Transaction Volume Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict


def accounting_top_accounts(dfs: Dict[str, pd.DataFrame], top_n: int = 15) -> dict:
    """
    Identify top accounts by transaction volume from accounting data.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
        top_n: Number of top accounts to return (default: 15)
    
    Returns:
        JSON-serializable dict with top accounts, chart data, summary statistics, and human-readable summary
    """
    # Get accounting data
    accounting_df = dfs.get("coqley_account_data", pd.DataFrame()).copy()
    
    if accounting_df.empty:
        return {
            "accounts": [],
            "chart_data": {
                "top_accounts": {"account_names": [], "total_activity": []},
                "debits_credits": {"account_names": [], "debits": [], "credits": []}
            },
            "summary": {
                "total_accounts": 0,
                "top_n": top_n,
                "total_activity_all_accounts": 0.0,
                "top_n_activity": 0.0,
                "top_n_percentage": 0.0,
                "currency": "USD"
            },
            "summary_text": "No accounting data available."
        }
    
    # Calculate total activity per account (sum of absolute values of debits and credits)
    accounting_df['Total Activity USD'] = accounting_df['m_dollar'].fillna(0).abs() + accounting_df['d_dollar'].fillna(0).abs()
    
    # Group by account
    account_summary = accounting_df.groupby('hisab_name').agg({
        'Total Activity USD': 'sum',
        'm_dollar': 'sum',  # Total debits
        'd_dollar': 'sum',  # Total credits
        'kaid': 'count'     # Number of transactions
    }).fillna(0)
    
    # Rename columns for clarity
    account_summary.columns = ['Total Activity (USD)', 'Total Debits (USD)', 
                              'Total Credits (USD)', 'Transaction Count']
    
    # Sort by total activity
    account_summary = account_summary.sort_values('Total Activity (USD)', ascending=False)
    
    # Get top N accounts
    top_accounts = account_summary.head(top_n)
    
    # Convert to list of dicts
    accounts = []
    for account_name, row in top_accounts.iterrows():
        accounts.append({
            "account_name": str(account_name),
            "total_activity": round(float(row['Total Activity (USD)']), 2),
            "total_debits": round(float(row['Total Debits (USD)']), 2),
            "total_credits": round(float(row['Total Credits (USD)']), 2),
            "transaction_count": int(row['Transaction Count'])
        })
    
    # Prepare chart data for LLM to recreate charts
    chart_data = {
        "top_accounts": {
            "account_names": [a["account_name"][:40] + "..." if len(a["account_name"]) > 40 else a["account_name"] 
                             for a in accounts],
            "total_activity": [a["total_activity"] for a in accounts],
            "chart_type": "barh",
            "title": f"Top {top_n} Accounts by Transaction Volume",
            "xlabel": "Total Activity (USD)",
            "ylabel": "Account",
            "orientation": "horizontal"
        },
        "debits_credits": {
            "account_names": [a["account_name"][:30] + "..." if len(a["account_name"]) > 30 else a["account_name"] 
                             for a in accounts[:10]],  # Top 10 for this chart
            "debits": [a["total_debits"] for a in accounts[:10]],
            "credits": [a["total_credits"] for a in accounts[:10]],
            "chart_type": "barh",
            "title": "Top 10 Accounts: Debits vs Credits",
            "xlabel": "Amount (USD)",
            "ylabel": "Account",
            "legend": ["Debits", "Credits"],
            "orientation": "horizontal"
        }
    }
    
    # Calculate summary statistics
    total_accounts = len(account_summary)
    total_activity_all = account_summary['Total Activity (USD)'].sum()
    top_n_activity = top_accounts['Total Activity (USD)'].sum()
    top_n_percentage = (top_n_activity / total_activity_all * 100) if total_activity_all > 0 else 0.0
    
    # Generate human-readable summary
    summary_parts = [f"Top accounts analysis across {total_accounts} unique accounts."]
    summary_parts.append(f"Total activity across all accounts: ${total_activity_all:,.2f}.")
    summary_parts.append(f"Top {top_n} accounts represent ${top_n_activity:,.2f} ({top_n_percentage:.1f}% of total activity).")
    
    if accounts:
        top_account = accounts[0]
        summary_parts.append(
            f"Highest activity account: {top_account['account_name']} "
            f"with ${top_account['total_activity']:,.2f} total activity "
            f"({top_account['transaction_count']} transactions)."
        )
        
        # Find account with most transactions
        most_transactions_account = max(accounts, key=lambda x: x['transaction_count'])
        if most_transactions_account['account_name'] != top_account['account_name']:
            summary_parts.append(
                f"Most transactions: {most_transactions_account['account_name']} "
                f"with {most_transactions_account['transaction_count']} transactions."
            )
    
    summary_text = " ".join(summary_parts)
    
    return {
        "accounts": accounts,
        "chart_data": chart_data,
        "summary": {
            "total_accounts": total_accounts,
            "top_n": top_n,
            "total_activity_all_accounts": round(total_activity_all, 2),
            "top_n_activity": round(top_n_activity, 2),
            "top_n_percentage": round(top_n_percentage, 2),
            "currency": "USD"
        },
        "summary_text": summary_text
    }
