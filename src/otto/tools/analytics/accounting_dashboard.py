"""
Account Activity Dashboard Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime


def accounting_dashboard(dfs: Dict[str, pd.DataFrame], top_n: int = 20) -> dict:
    """
    Generate account activity dashboard showing transaction volume, frequency, and activity patterns.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
        top_n: Number of top accounts to return (default: 20)
    
    Returns:
        JSON-serializable dict with account activity metrics, chart data, summary statistics, and human-readable summary
    """
    # Get accounting data
    accounting_df = dfs.get("coqley_account_data", pd.DataFrame()).copy()
    
    if accounting_df.empty:
        return {
            "accounts": [],
            "chart_data": {
                "activity_volume": {"account_names": [], "total_activity": []},
                "transaction_count": {"account_names": [], "transaction_count": []},
                "activity_timeline": {"accounts": [], "dates": [], "activity": []}
            },
            "summary": {
                "total_accounts": 0,
                "total_transactions": 0,
                "total_activity": 0.0,
                "date_range": {"start": None, "end": None},
                "average_transactions_per_account": 0.0,
                "average_activity_per_account": 0.0,
                "currency": "USD"
            },
            "summary_text": "No accounting data available."
        }
    
    # Ensure date column is datetime
    accounting_df['date'] = pd.to_datetime(accounting_df['date'], errors='coerce')
    
    # Calculate total activity per account (sum of absolute values of debits and credits)
    accounting_df['Total Activity USD'] = accounting_df['m_dollar'].fillna(0).abs() + accounting_df['d_dollar'].fillna(0).abs()
    
    # Group by account and calculate metrics
    account_summary = accounting_df.groupby('hisab_name').agg({
        'Total Activity USD': 'sum',
        'd_dollar': ['sum', 'count'],  # Total credits and count of credit transactions
        'm_dollar': ['sum', 'count'],  # Total debits and count of debit transactions
        'kaid': 'nunique',  # Unique transaction IDs
        'date': ['min', 'max']  # First and last transaction dates
    }).fillna(0)
    
    # Flatten column names
    account_summary.columns = [
        'Total Activity (USD)',
        'Total Credits (USD)',
        'Credit Transactions',
        'Total Debits (USD)',
        'Debit Transactions',
        'Unique Transactions',
        'First Transaction Date',
        'Last Transaction Date'
    ]
    
    # Calculate transaction count (total transactions, not unique)
    account_summary['Total Transactions'] = account_summary['Credit Transactions'] + account_summary['Debit Transactions']
    
    # Calculate activity duration in days
    account_summary['Activity Duration (days)'] = (
        account_summary['Last Transaction Date'] - account_summary['First Transaction Date']
    ).dt.days.fillna(0)
    
    # Calculate average activity per transaction
    account_summary['Avg Activity per Transaction'] = (
        account_summary['Total Activity (USD)'] / account_summary['Total Transactions'].replace(0, np.nan)
    ).fillna(0)
    
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
            "total_credits": round(float(row['Total Credits (USD)']), 2),
            "total_debits": round(float(row['Total Debits (USD)']), 2),
            "unique_transactions": int(row['Unique Transactions']),
            "total_transactions": int(row['Total Transactions']),
            "credit_transactions": int(row['Credit Transactions']),
            "debit_transactions": int(row['Debit Transactions']),
            "first_transaction_date": str(row['First Transaction Date']) if pd.notna(row['First Transaction Date']) else None,
            "last_transaction_date": str(row['Last Transaction Date']) if pd.notna(row['Last Transaction Date']) else None,
            "activity_duration_days": int(row['Activity Duration (days)']),
            "avg_activity_per_transaction": round(float(row['Avg Activity per Transaction']), 2)
        })
    
    # Prepare chart data
    chart_data = {
        "activity_volume": {
            "account_names": [a["account_name"][:40] + "..." if len(a["account_name"]) > 40 else a["account_name"] 
                             for a in accounts],
            "total_activity": [a["total_activity"] for a in accounts],
            "chart_type": "barh",
            "title": f"Top {top_n} Accounts by Total Activity Volume",
            "xlabel": "Total Activity (USD)",
            "ylabel": "Account",
            "orientation": "horizontal"
        },
        "transaction_count": {
            "account_names": [a["account_name"][:40] + "..." if len(a["account_name"]) > 40 else a["account_name"] 
                             for a in accounts],
            "transaction_count": [a["total_transactions"] for a in accounts],
            "chart_type": "barh",
            "title": f"Top {top_n} Accounts by Transaction Count",
            "xlabel": "Number of Transactions",
            "ylabel": "Account",
            "orientation": "horizontal"
        },
        "activity_overview": {
            "account_names": [a["account_name"][:30] + "..." if len(a["account_name"]) > 30 else a["account_name"] 
                             for a in accounts[:15]],  # Top 15 for readability
            "total_activity": [a["total_activity"] for a in accounts[:15]],
            "unique_transactions": [a["unique_transactions"] for a in accounts[:15]],
            "chart_type": "bar",
            "title": "Top 15 Accounts: Activity vs Transaction Count",
            "xlabel": "Account",
            "ylabel": "Amount / Count",
            "legend": ["Total Activity (USD)", "Unique Transactions"],
            "orientation": "vertical"
        }
    }
    
    # Calculate summary statistics
    total_accounts = len(account_summary)
    total_transactions = accounting_df.shape[0]
    total_activity_all = account_summary['Total Activity (USD)'].sum()
    top_n_activity = top_accounts['Total Activity (USD)'].sum()
    top_n_percentage = (top_n_activity / total_activity_all * 100) if total_activity_all > 0 else 0.0
    
    # Date range
    date_range = {
        "start": str(accounting_df['date'].min()) if pd.notna(accounting_df['date'].min()) else None,
        "end": str(accounting_df['date'].max()) if pd.notna(accounting_df['date'].max()) else None
    }
    
    # Calculate averages
    avg_transactions_per_account = total_transactions / total_accounts if total_accounts > 0 else 0.0
    avg_activity_per_account = total_activity_all / total_accounts if total_accounts > 0 else 0.0
    
    # Generate human-readable summary
    summary_parts = [f"Account activity dashboard analysis across {total_accounts} unique accounts."]
    summary_parts.append(f"Total transactions: {total_transactions:,}.")
    summary_parts.append(f"Total activity across all accounts: ${total_activity_all:,.2f}.")
    summary_parts.append(f"Top {top_n} accounts represent ${top_n_activity:,.2f} ({top_n_percentage:.1f}% of total activity).")
    summary_parts.append(f"Average transactions per account: {avg_transactions_per_account:.1f}.")
    summary_parts.append(f"Average activity per account: ${avg_activity_per_account:,.2f}.")
    
    if date_range["start"] and date_range["end"]:
        summary_parts.append(f"Date range: {date_range['start'][:10]} to {date_range['end'][:10]}.")
    
    if accounts:
        top_account = accounts[0]
        summary_parts.append(
            f"Highest activity account: {top_account['account_name']} "
            f"with ${top_account['total_activity']:,.2f} total activity "
            f"({top_account['total_transactions']} transactions, "
            f"{top_account['unique_transactions']} unique transaction IDs)."
        )
        
        # Find account with most transactions
        most_transactions_account = max(accounts, key=lambda x: x['total_transactions'])
        if most_transactions_account['account_name'] != top_account['account_name']:
            summary_parts.append(
                f"Most transactions: {most_transactions_account['account_name']} "
                f"with {most_transactions_account['total_transactions']} transactions."
            )
        
        # Find account with highest average per transaction
        highest_avg_account = max([a for a in accounts if a['avg_activity_per_transaction'] > 0], 
                                 key=lambda x: x['avg_activity_per_transaction'], 
                                 default=None)
        if highest_avg_account and highest_avg_account['account_name'] != top_account['account_name']:
            summary_parts.append(
                f"Highest average activity per transaction: {highest_avg_account['account_name']} "
                f"with ${highest_avg_account['avg_activity_per_transaction']:,.2f} per transaction."
            )
    
    summary_text = " ".join(summary_parts)
    
    return {
        "accounts": accounts,
        "chart_data": chart_data,
        "summary": {
            "total_accounts": total_accounts,
            "total_transactions": total_transactions,
            "total_activity": round(total_activity_all, 2),
            "top_n": top_n,
            "top_n_activity": round(top_n_activity, 2),
            "top_n_percentage": round(top_n_percentage, 2),
            "date_range": date_range,
            "average_transactions_per_account": round(avg_transactions_per_account, 2),
            "average_activity_per_account": round(avg_activity_per_account, 2),
            "currency": "USD"
        },
        "summary_text": summary_text
    }

