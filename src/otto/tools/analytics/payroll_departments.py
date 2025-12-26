"""
Payroll Cost by Department Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict


def payroll_by_department(dfs: Dict[str, pd.DataFrame]) -> dict:
    """
    Calculate payroll costs by department from payroll data.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
    
    Returns:
        JSON-serializable dict with department costs, chart data, summary statistics, and human-readable summary
    """
    # Get payroll data
    payroll_df = dfs.get("coqley_payroll_data", pd.DataFrame()).copy()
    
    if payroll_df.empty:
        return {
            "departments": [],
            "chart_data": {
                "department_costs": {"departments": [], "total_costs": []},
                "cost_distribution": {"departments": [], "percentages": []}
            },
            "summary": {
                "total_payroll": 0.0,
                "average_per_employee": 0.0,
                "total_employees": 0,
                "number_of_departments": 0,
                "currency": "USD"
            },
            "summary_text": "No payroll data available."
        }
    
    # Clean up the data
    payroll_df = payroll_df[payroll_df['name'].notna() & payroll_df['dep'].notna()]
    
    # Find the cost column (Net Pay or Monthly)
    cost_col = None
    for col in payroll_df.columns:
        if 'net' in str(col).lower() and 'pay' in str(col).lower():
            cost_col = col
            break
    
    if cost_col is None or cost_col not in payroll_df.columns:
        cost_col = 'monthly'
    
    # Group by department
    dept_summary = payroll_df.groupby('dep').agg({
        cost_col: ['sum', 'mean', 'count'],
        'name': 'count'
    }).fillna(0)
    
    dept_summary.columns = ['Total Cost', 'Average Cost', 'Transaction Count', 'Employee Count']
    dept_summary = dept_summary.sort_values('Total Cost', ascending=False)
    
    # Calculate percentages
    total_payroll = dept_summary['Total Cost'].sum()
    dept_summary['Percentage'] = (dept_summary['Total Cost'] / total_payroll * 100).round(2)
    
    # Convert to list of dicts
    departments = []
    for dept, row in dept_summary.iterrows():
        departments.append({
            "department": str(dept),
            "total_cost": round(float(row['Total Cost']), 2),
            "average_cost": round(float(row['Average Cost']), 2),
            "employee_count": int(row['Employee Count']),
            "percentage": round(float(row['Percentage']), 2)
        })
    
    # Prepare chart data for LLM to recreate charts
    chart_data = {
        "department_costs": {
            "departments": [d["department"] for d in departments],
            "total_costs": [d["total_cost"] for d in departments],
            "chart_type": "bar",
            "title": "Total Payroll Cost by Department",
            "xlabel": "Department",
            "ylabel": "Total Payroll Cost (USD)",
            "rotation": 45
        },
        "cost_distribution": {
            "departments": [d["department"] for d in departments],
            "percentages": [d["percentage"] for d in departments],
            "chart_type": "pie",
            "title": "Payroll Cost Distribution by Department",
            "autopct": "%1.1f%%"
        }
    }
    
    # Calculate summary statistics
    total_employees = dept_summary['Employee Count'].sum()
    avg_per_employee = total_payroll / total_employees if total_employees > 0 else 0.0
    
    # Generate human-readable summary
    summary_parts = [f"Payroll analysis across {len(departments)} departments."]
    summary_parts.append(f"Total payroll cost: ${total_payroll:,.2f}.")
    summary_parts.append(f"Total employees: {total_employees}.")
    summary_parts.append(f"Average cost per employee: ${avg_per_employee:,.2f}.")
    
    if departments:
        top_dept = departments[0]
        summary_parts.append(
            f"Highest cost department: {top_dept['department']} "
            f"with ${top_dept['total_cost']:,.2f} total "
            f"({top_dept['employee_count']} employees, {top_dept['percentage']:.1f}% of total)."
        )
        
        if len(departments) > 1:
            bottom_dept = departments[-1]
            summary_parts.append(
                f"Lowest cost department: {bottom_dept['department']} "
                f"with ${bottom_dept['total_cost']:,.2f} total "
                f"({bottom_dept['employee_count']} employees)."
            )
    
    summary_text = " ".join(summary_parts)
    
    return {
        "departments": departments,
        "chart_data": chart_data,
        "summary": {
            "total_payroll": round(total_payroll, 2),
            "average_per_employee": round(avg_per_employee, 2),
            "total_employees": int(total_employees),
            "number_of_departments": len(departments),
            "currency": "USD"
        },
        "summary_text": summary_text
    }

