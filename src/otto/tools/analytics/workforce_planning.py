"""
Workforce Planning Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime


def workforce_planning(dfs: Dict[str, pd.DataFrame]) -> dict:
    """
    Analyze current workforce composition and structure.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
    
    Returns:
        JSON-serializable dict with workforce composition, chart data, summary statistics, and human-readable summary
    """
    # Get payroll data
    payroll_df = dfs.get("coqley_payroll_data", pd.DataFrame()).copy()
    
    if payroll_df.empty:
        return {
            "departments": [],
            "positions": [],
            "tenure_distribution": [],
            "branch_distribution": [],
            "status_distribution": [],
            "chart_data": {},
            "summary": {
                "total_employees": 0,
                "total_monthly_payroll": 0.0,
                "average_salary": 0.0,
                "number_of_departments": 0,
                "number_of_positions": 0,
                "currency": "USD"
            },
            "summary_text": "No payroll data available."
        }
    
    # Clean up the data
    payroll_df = payroll_df[payroll_df['name'].notna() & payroll_df['dep'].notna()]
    
    # Convert Starting Date to datetime
    payroll_df['Starting Date'] = pd.to_datetime(payroll_df['starting_date'], errors='coerce')
    
    # Calculate tenure (years with company)
    current_date = datetime.now()
    payroll_df['Tenure (Years)'] = (current_date - payroll_df['Starting Date']).dt.days / 365.25
    payroll_df['Tenure (Years)'] = payroll_df['Tenure (Years)'].fillna(0)
    
    # 1. Workforce Composition by Department
    dept_composition = payroll_df.groupby('dep').agg({
        'name': 'count',
        'monthly': ['sum', 'mean'],
        'Tenure (Years)': 'mean'
    }).round(2)
    
    dept_composition.columns = ['Headcount', 'Total Monthly Cost', 'Avg Monthly Salary', 'Avg Tenure (Years)']
    dept_composition = dept_composition.sort_values('Headcount', ascending=False)
    
    departments = []
    for dept, row in dept_composition.iterrows():
        departments.append({
            "department": str(dept),
            "headcount": int(row['Headcount']),
            "total_monthly_cost": round(float(row['Total Monthly Cost']), 2),
            "average_salary": round(float(row['Avg Monthly Salary']), 2),
            "average_tenure_years": round(float(row['Avg Tenure (Years)']), 2)
        })
    
    # 2. Position Distribution
    position_dist = payroll_df.groupby('position').agg({
        'name': 'count',
        'monthly': 'mean'
    }).round(2)
    position_dist.columns = ['Count', 'Avg Salary']
    position_dist = position_dist.sort_values('Count', ascending=False).head(15)
    
    positions = []
    for position, row in position_dist.iterrows():
        positions.append({
            "position": str(position),
            "count": int(row['Count']),
            "average_salary": round(float(row['Avg Salary']), 2)
        })
    
    # 3. Tenure Analysis
    payroll_df['Tenure Category'] = pd.cut(
        payroll_df['Tenure (Years)'], 
        bins=[0, 1, 3, 5, 10, 100],
        labels=['< 1 year', '1-3 years', '3-5 years', '5-10 years', '10+ years']
    )
    
    tenure_dist = payroll_df.groupby('Tenure Category', observed=True).agg({
        'name': 'count',
        'monthly': 'mean'
    }).round(2)
    tenure_dist.columns = ['Count', 'Avg Salary']
    tenure_dist['Percentage'] = (tenure_dist['Count'] / tenure_dist['Count'].sum() * 100).round(1)
    
    tenure_distribution = []
    for category, row in tenure_dist.iterrows():
        if pd.notna(category):
            tenure_distribution.append({
                "category": str(category),
                "count": int(row['Count']),
                "average_salary": round(float(row['Avg Salary']), 2),
                "percentage": round(float(row['Percentage']), 2)
            })
    
    # 4. Branch Distribution
    branch_dist = payroll_df.groupby('branch').agg({
        'name': 'count',
        'monthly': 'sum'
    }).round(2)
    branch_dist.columns = ['Headcount', 'Total Monthly Cost']
    branch_dist = branch_dist.sort_values('Headcount', ascending=False)
    branch_dist['Percentage'] = (branch_dist['Headcount'] / branch_dist['Headcount'].sum() * 100).round(1)
    
    branch_distribution = []
    for branch, row in branch_dist.iterrows():
        branch_distribution.append({
            "branch": str(branch),
            "headcount": int(row['Headcount']),
            "total_monthly_cost": round(float(row['Total Monthly Cost']), 2),
            "percentage": round(float(row['Percentage']), 2)
        })
    
    # 5. Status Distribution
    status_dist = payroll_df.groupby('status').agg({
        'name': 'count',
        'monthly': 'mean'
    }).round(2)
    status_dist.columns = ['Count', 'Avg Salary']
    status_dist['Percentage'] = (status_dist['Count'] / status_dist['Count'].sum() * 100).round(1)
    
    status_distribution = []
    for status, row in status_dist.iterrows():
        status_distribution.append({
            "status": str(status),
            "count": int(row['Count']),
            "average_salary": round(float(row['Avg Salary']), 2),
            "percentage": round(float(row['Percentage']), 2)
        })
    
    # Prepare chart data for LLM to recreate charts
    chart_data = {
        "headcount_by_department": {
            "departments": [d["department"] for d in departments],
            "headcount": [d["headcount"] for d in departments],
            "chart_type": "barh",
            "title": "Workforce Headcount by Department",
            "xlabel": "Number of Employees",
            "ylabel": "Department",
            "orientation": "horizontal"
        },
        "tenure_distribution": {
            "categories": [t["category"] for t in tenure_distribution],
            "counts": [t["count"] for t in tenure_distribution],
            "chart_type": "bar",
            "title": "Workforce Tenure Distribution",
            "xlabel": "Tenure Category",
            "ylabel": "Number of Employees"
        },
        "top_positions": {
            "positions": [p["position"] for p in positions[:10]],
            "counts": [p["count"] for p in positions[:10]],
            "chart_type": "barh",
            "title": "Top 10 Positions by Headcount",
            "xlabel": "Number of Employees",
            "ylabel": "Position",
            "orientation": "horizontal"
        },
        "branch_distribution": {
            "branches": [b["branch"] for b in branch_distribution],
            "headcount": [b["headcount"] for b in branch_distribution],
            "percentages": [b["percentage"] for b in branch_distribution],
            "chart_type": "pie",
            "title": "Workforce Distribution by Branch",
            "autopct": "%1.1f%%"
        }
    }
    
    # Calculate summary statistics
    total_employees = len(payroll_df)
    total_monthly_payroll = payroll_df['monthly'].sum()
    avg_salary = payroll_df['monthly'].mean()
    num_departments = payroll_df['dep'].nunique()
    num_positions = payroll_df['position'].nunique()
    
    # Generate human-readable summary
    summary_parts = [f"Workforce planning analysis for {total_employees} employees."]
    summary_parts.append(f"Total monthly payroll: ${total_monthly_payroll:,.2f}.")
    summary_parts.append(f"Average monthly salary: ${avg_salary:,.2f}.")
    summary_parts.append(f"Departments: {num_departments}, Positions: {num_positions}.")
    
    if departments:
        largest_dept = max(departments, key=lambda x: x['headcount'])
        summary_parts.append(
            f"Largest department: {largest_dept['department']} "
            f"with {largest_dept['headcount']} employees."
        )
    
    if tenure_distribution:
        largest_tenure = max(tenure_distribution, key=lambda x: x['count'])
        summary_parts.append(
            f"Largest tenure group: {largest_tenure['category']} "
            f"with {largest_tenure['count']} employees ({largest_tenure['percentage']:.1f}%)."
        )
    
    summary_text = " ".join(summary_parts)
    
    return {
        "departments": departments,
        "positions": positions,
        "tenure_distribution": tenure_distribution,
        "branch_distribution": branch_distribution,
        "status_distribution": status_distribution,
        "chart_data": chart_data,
        "summary": {
            "total_employees": int(total_employees),
            "total_monthly_payroll": round(total_monthly_payroll, 2),
            "average_salary": round(avg_salary, 2),
            "number_of_departments": int(num_departments),
            "number_of_positions": int(num_positions),
            "currency": "USD"
        },
        "summary_text": summary_text
    }

