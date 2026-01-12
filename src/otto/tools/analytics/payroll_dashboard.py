"""
Payroll Dashboard Analysis
Comprehensive payroll analytics with department, position, employee, and cost breakdowns.
"""

import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime


def payroll_dashboard(dfs: Dict[str, pd.DataFrame]) -> dict:
    """
    Generate comprehensive payroll dashboard with department, position, employee, and cost analysis.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
    
    Returns:
        JSON-serializable dict with payroll metrics, chart data, summary statistics, and human-readable summary
    """
    # Get payroll data
    payroll_df = dfs.get("coqley_payroll_data", pd.DataFrame()).copy()
    
    if payroll_df.empty:
        return {
            "departments": [],
            "positions": [],
            "employees": [],
            "chart_data": {
                "department_costs": {"departments": [], "total_costs": []},
                "position_costs": {"positions": [], "total_costs": []},
                "cost_breakdown": {"categories": [], "amounts": []},
                "monthly_trends": {"months": [], "total_costs": []}
            },
            "summary": {
                "total_employees": 0,
                "total_payroll_cost": 0.0,
                "average_cost_per_employee": 0.0,
                "number_of_departments": 0,
                "number_of_positions": 0,
                "currency": "USD"
            },
            "summary_text": "No payroll data available."
        }
    
    # Clean up the data - remove rows with missing essential fields
    payroll_df = payroll_df[payroll_df['name'].notna() & payroll_df['dep'].notna()].copy()
    
    # Calculate tenure if starting_date is available
    if 'starting_date' in payroll_df.columns:
        payroll_df['starting_date_parsed'] = pd.to_datetime(payroll_df['starting_date'], errors='coerce')
        current_date = datetime.now()
        payroll_df['tenure_years'] = (current_date - payroll_df['starting_date_parsed']).dt.days / 365.25
        payroll_df['tenure_years'] = payroll_df['tenure_years'].fillna(0)
    
    # Identify cost column - try net_to_\npay, monthly, or cost
    cost_col = None
    for col in ['net_to_\npay', 'monthly', 'cost']:
        if col in payroll_df.columns:
            cost_col = col
            break
    
    if cost_col is None:
        # If no cost column found, try to find any numeric column that might represent cost
        numeric_cols = payroll_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            cost_col = numeric_cols[0]
        else:
            return {
                "departments": [],
                "positions": [],
                "employees": [],
                "chart_data": {},
                "summary": {"total_employees": 0, "total_payroll_cost": 0.0, "currency": "USD"},
                "summary_text": "No valid cost column found in payroll data."
            }
    
    # Convert cost column to numeric, handling any string values
    payroll_df[cost_col] = pd.to_numeric(payroll_df[cost_col], errors='coerce').fillna(0)
    
    # Calculate additional metrics if columns exist
    if 'tax' in payroll_df.columns:
        payroll_df['tax'] = pd.to_numeric(payroll_df['tax'], errors='coerce').fillna(0)
    if 'nssf' in payroll_df.columns:
        payroll_df['nssf'] = pd.to_numeric(payroll_df['nssf'], errors='coerce').fillna(0)
    if 'transport' in payroll_df.columns:
        payroll_df['transport'] = pd.to_numeric(payroll_df['transport'], errors='coerce').fillna(0)
    if 'family_allowance' in payroll_df.columns:
        payroll_df['family_allowance'] = pd.to_numeric(payroll_df['family_allowance'], errors='coerce').fillna(0)
    if 'vac' in payroll_df.columns:
        payroll_df['vac'] = pd.to_numeric(payroll_df['vac'], errors='coerce').fillna(0)
    if 'sick' in payroll_df.columns:
        payroll_df['sick'] = pd.to_numeric(payroll_df['sick'], errors='coerce').fillna(0)
    
    # Calculate gross cost (net pay + taxes + benefits if available)
    payroll_df['gross_cost'] = payroll_df[cost_col].fillna(0)
    if 'tax' in payroll_df.columns:
        payroll_df['gross_cost'] += payroll_df['tax'].fillna(0)
    if 'nssf' in payroll_df.columns:
        payroll_df['gross_cost'] += payroll_df['nssf'].fillna(0)
    
    # Department Analysis
    dept_summary = payroll_df.groupby('dep').agg({
        cost_col: ['sum', 'mean', 'count'],
        'gross_cost': 'sum',
        'name': 'nunique'  # Unique employee count
    }).fillna(0)
    
    dept_summary.columns = ['Total Cost', 'Average Cost', 'Record Count', 'Gross Cost', 'Employee Count']
    dept_summary = dept_summary.sort_values('Total Cost', ascending=False)
    
    total_payroll = float(dept_summary['Total Cost'].sum())
    dept_summary['Percentage'] = (dept_summary['Total Cost'] / total_payroll * 100).round(2)
    
    departments = []
    for dept, row in dept_summary.iterrows():
        departments.append({
            "department": str(dept),
            "total_cost": round(float(row['Total Cost']), 2),
            "gross_cost": round(float(row['Gross Cost']), 2),
            "average_cost": round(float(row['Average Cost']), 2),
            "employee_count": int(row['Employee Count']),
            "record_count": int(row['Record Count']),
            "percentage": round(float(row['Percentage']), 2)
        })
    
    # Position Analysis
    positions = []
    if 'position' in payroll_df.columns:
        position_summary = payroll_df.groupby('position').agg({
            cost_col: ['sum', 'mean', 'count'],
            'name': 'nunique'
        }).fillna(0)
        
        position_summary.columns = ['Total Cost', 'Average Cost', 'Record Count', 'Employee Count']
        position_summary = position_summary.sort_values('Total Cost', ascending=False)
        
        for pos, row in position_summary.iterrows():
            if pd.notna(pos) and str(pos).strip():
                positions.append({
                    "position": str(pos),
                    "total_cost": round(float(row['Total Cost']), 2),
                    "average_cost": round(float(row['Average Cost']), 2),
                    "employee_count": int(row['Employee Count']),
                    "record_count": int(row['Record Count'])
                })
    
    # Employee-level summary (top employees by cost)
    employee_summary = payroll_df.groupby('name').agg({
        cost_col: ['sum', 'mean', 'count'],
        'dep': 'first',
        'position': 'first'
    }).fillna(0)
    
    employee_summary.columns = ['Total Cost', 'Average Cost', 'Record Count', 'Department', 'Position']
    employee_summary = employee_summary.sort_values('Total Cost', ascending=False).head(20)
    
    employees = []
    for name, row in employee_summary.iterrows():
        if pd.notna(name) and str(name).strip():
            employees.append({
                "employee_name": str(name),
                "department": str(row['Department']) if pd.notna(row['Department']) else 'Unknown',
                "position": str(row['Position']) if pd.notna(row['Position']) else 'Unknown',
                "total_cost": round(float(row['Total Cost']), 2),
                "average_cost": round(float(row['Average Cost']), 2),
                "record_count": int(row['Record Count'])
            })
    
    # Monthly Trends (if month column exists)
    monthly_trends = []
    monthly_trends_data = {"months": [], "total_costs": []}
    if 'month' in payroll_df.columns:
        monthly_summary = payroll_df.groupby('month').agg({
            cost_col: 'sum',
            'name': 'nunique'
        }).fillna(0)
        monthly_summary = monthly_summary.sort_index()
        
        for month, row in monthly_summary.iterrows():
            if pd.notna(month):
                monthly_trends.append({
                    "month": str(month),
                    "total_cost": round(float(row[cost_col]), 2),
                    "employee_count": int(row['name'])
                })
                monthly_trends_data["months"].append(str(month))
                monthly_trends_data["total_costs"].append(round(float(row[cost_col]), 2))
    
    # Cost Breakdown (taxes, benefits, etc.)
    cost_breakdown = {
        "categories": ["Net Pay"],
        "amounts": [float(round(total_payroll, 2))]
    }
    
    if 'tax' in payroll_df.columns:
        total_tax = float(payroll_df['tax'].sum())
        cost_breakdown["categories"].append("Taxes")
        cost_breakdown["amounts"].append(float(round(total_tax, 2)))
    
    if 'nssf' in payroll_df.columns:
        total_nssf = float(payroll_df['nssf'].sum())
        cost_breakdown["categories"].append("NSSF")
        cost_breakdown["amounts"].append(float(round(total_nssf, 2)))
    
    if 'transport' in payroll_df.columns:
        total_transport = float(payroll_df['transport'].sum())
        if total_transport > 0:
            cost_breakdown["categories"].append("Transport")
            cost_breakdown["amounts"].append(float(round(total_transport, 2)))
    
    if 'family_allowance' in payroll_df.columns:
        total_family = float(payroll_df['family_allowance'].sum())
        if total_family > 0:
            cost_breakdown["categories"].append("Family Allowance")
            cost_breakdown["amounts"].append(float(round(total_family, 2)))
    
    # Prepare chart data
    chart_data = {
        "department_costs": {
            "departments": [d["department"] for d in departments],
            "total_costs": [d["total_cost"] for d in departments],
            "chart_type": "bar",
            "title": "Total Payroll Cost by Department",
            "xlabel": "Department",
            "ylabel": "Total Cost (USD)",
            "rotation": 45
        },
        "position_costs": {
            "positions": [p["position"][:30] + "..." if len(p["position"]) > 30 else p["position"] 
                         for p in positions[:15]],  # Top 15 positions
            "total_costs": [p["total_cost"] for p in positions[:15]],
            "chart_type": "bar",
            "title": "Top 15 Positions by Payroll Cost",
            "xlabel": "Position",
            "ylabel": "Total Cost (USD)",
            "rotation": 45
        },
        "cost_breakdown": {
            "categories": cost_breakdown["categories"],
            "amounts": cost_breakdown["amounts"],
            "chart_type": "pie",
            "title": "Payroll Cost Breakdown",
            "autopct": "%1.1f%%"
        }
    }
    
    # Add monthly trends chart if data available
    if monthly_trends_data["months"]:
        chart_data["monthly_trends"] = {
            "months": monthly_trends_data["months"],
            "total_costs": monthly_trends_data["total_costs"],
            "chart_type": "line",
            "title": "Monthly Payroll Trends",
            "xlabel": "Month",
            "ylabel": "Total Cost (USD)",
            "marker": "o"
        }
    
    # Salary vs Tenure Scatter Chart (by employee, colored by department)
    if 'tenure_years' in payroll_df.columns and cost_col in payroll_df.columns:
        # Get average salary and tenure per employee
        employee_scatter_data = payroll_df.groupby(['name', 'dep']).agg({
            cost_col: 'mean',  # Average salary
            'tenure_years': 'mean'  # Average tenure (should be same per employee)
        }).reset_index()
        employee_scatter_data = employee_scatter_data[
            (employee_scatter_data[cost_col] > 0) & 
            (employee_scatter_data['tenure_years'] > 0) &
            (employee_scatter_data['dep'].notna())
        ].copy()
        
        if not employee_scatter_data.empty:
            # Prepare scatter chart data grouped by department
            scatter_by_dept = {}
            for dept in employee_scatter_data['dep'].unique():
                dept_data = employee_scatter_data[employee_scatter_data['dep'] == dept]
                scatter_by_dept[str(dept)] = {
                    "salaries": [round(float(x), 2) for x in dept_data[cost_col].tolist()],
                    "tenures": [round(float(y), 2) for y in dept_data['tenure_years'].tolist()],
                    "employees": [str(name) for name in dept_data['name'].tolist()]
                }
            
            chart_data["salary_tenure_scatter"] = {
                "chart_type": "scatter",
                "title": "Employee Salary vs Tenure by Department",
                "xlabel": f"Salary ({cost_col}) (USD)",
                "ylabel": "Tenure (Years)",
                "departments": scatter_by_dept,
                "legend": "Department"
            }
    
    # Calculate summary statistics
    total_employees = int(payroll_df['name'].nunique())
    avg_cost_per_employee = float(total_payroll / total_employees if total_employees > 0 else 0.0)
    
    # Generate human-readable summary
    summary_parts = [f"Payroll dashboard analysis across {len(departments)} departments."]
    summary_parts.append(f"Total employees: {total_employees}.")
    summary_parts.append(f"Total payroll cost: ${total_payroll:,.2f}.")
    summary_parts.append(f"Average cost per employee: ${avg_cost_per_employee:,.2f}.")
    
    if departments:
        top_dept = departments[0]
        summary_parts.append(
            f"Highest cost department: {top_dept['department']} "
            f"with ${top_dept['total_cost']:,.2f} total cost "
            f"({top_dept['employee_count']} employees, {top_dept['percentage']:.1f}% of total)."
        )
    
    if positions:
        top_position = positions[0]
        summary_parts.append(
            f"Highest cost position: {top_position['position']} "
            f"with ${top_position['total_cost']:,.2f} total cost "
            f"({top_position['employee_count']} employees)."
        )
    
    if employees:
        top_employee = employees[0]
        summary_parts.append(
            f"Highest cost employee: {top_employee['employee_name']} "
            f"({top_employee['department']}, {top_employee['position']}) "
            f"with ${top_employee['total_cost']:,.2f} total cost."
        )
    
    if monthly_trends:
        summary_parts.append(f"Monthly trends available for {len(monthly_trends)} months.")
    
    summary_text = " ".join(summary_parts)
    
    return {
        "departments": departments,
        "positions": positions,
        "employees": employees,
        "monthly_trends": monthly_trends,
        "chart_data": chart_data,
        "summary": {
            "total_employees": int(total_employees),
            "total_payroll_cost": float(round(total_payroll, 2)),
            "average_cost_per_employee": float(round(avg_cost_per_employee, 2)),
            "number_of_departments": int(len(departments)),
            "number_of_positions": int(len(positions)),
            "currency": "USD"
        },
        "summary_text": summary_text
    }

