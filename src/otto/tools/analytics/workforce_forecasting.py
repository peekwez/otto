"""
Workforce Forecasting Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime


def workforce_forecasting(dfs: Dict[str, pd.DataFrame]) -> dict:
    """
    Project future workforce needs and payroll costs based on different growth scenarios.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
    
    Returns:
        JSON-serializable dict with forecasts, chart data, summary statistics, and human-readable summary
    """
    # Get payroll data
    payroll_df = dfs.get("coqley_payroll_data", pd.DataFrame()).copy()
    
    if payroll_df.empty:
        return {
            "scenarios": [],
            "department_forecast": [],
            "monthly_projection": [],
            "hiring_needs": {},
            "chart_data": {},
            "summary": {
                "current_headcount": 0,
                "current_monthly_payroll": 0.0,
                "current_annual_payroll": 0.0,
                "currency": "USD"
            },
            "summary_text": "No payroll data available."
        }
    
    # Clean up the data
    payroll_df = payroll_df[payroll_df['name'].notna() & payroll_df['dep'].notna()]
    
    # Current State
    current_headcount = len(payroll_df)
    current_monthly_payroll = payroll_df['monthly'].sum()
    current_avg_salary = payroll_df['monthly'].mean()
    current_annual_payroll = current_monthly_payroll * 12
    
    # Department baseline
    dept_baseline = payroll_df.groupby('dep').agg({
        'name': 'count',
        'monthly': 'sum'
    }).round(2)
    dept_baseline.columns = ['Headcount', 'Monthly Cost']
    dept_baseline['Monthly Cost'] = pd.to_numeric(dept_baseline['Monthly Cost'], errors='coerce')
    dept_baseline['Annual Cost'] = dept_baseline['Monthly Cost'] * 12
    
    # Forecasting Scenarios
    scenarios_config = {
        'Conservative (0% growth)': 0.00,
        'Moderate (5% growth)': 0.05,
        'Aggressive (10% growth)': 0.10,
        'High Growth (15% growth)': 0.15
    }
    
    scenarios = []
    for scenario_name, growth_rate in scenarios_config.items():
        projected_headcount = int(current_headcount * (1 + growth_rate))
        headcount_change = projected_headcount - current_headcount
        projected_monthly_payroll = current_monthly_payroll * (1 + growth_rate)
        projected_annual_payroll = projected_monthly_payroll * 12
        payroll_increase = (projected_monthly_payroll - current_monthly_payroll) * 12
        
        scenarios.append({
            "scenario_name": scenario_name,
            "growth_rate": round(growth_rate * 100, 1),
            "current_headcount": int(current_headcount),
            "projected_headcount": int(projected_headcount),
            "headcount_change": int(headcount_change),
            "current_annual_payroll": round(current_annual_payroll, 2),
            "projected_annual_payroll": round(projected_annual_payroll, 2),
            "payroll_increase": round(payroll_increase, 2)
        })
    
    # Department-level forecasting (Moderate 5% Growth Scenario)
    dept_forecast = dept_baseline.copy()
    dept_forecast['Projected Headcount'] = (dept_forecast['Headcount'] * 1.05).round().astype(int)
    dept_forecast['Headcount Change'] = dept_forecast['Projected Headcount'] - dept_forecast['Headcount']
    dept_forecast['Projected Annual Cost'] = (dept_forecast['Annual Cost'] * 1.05).round(2)
    dept_forecast['Cost Increase'] = dept_forecast['Projected Annual Cost'] - dept_forecast['Annual Cost']
    
    department_forecast = []
    for dept, row in dept_forecast.iterrows():
        department_forecast.append({
            "department": str(dept),
            "current_headcount": int(row['Headcount']),
            "projected_headcount": int(row['Projected Headcount']),
            "headcount_change": int(row['Headcount Change']),
            "current_annual_cost": round(float(row['Annual Cost']), 2),
            "projected_annual_cost": round(float(row['Projected Annual Cost']), 2),
            "cost_increase": round(float(row['Cost Increase']), 2)
        })
    
    # Hiring needs analysis
    attrition_rate = 0.05
    annual_attrition = int(current_headcount * attrition_rate)
    moderate_growth = int(current_headcount * 0.05)
    total_hiring_needs = annual_attrition + moderate_growth
    estimated_hiring_cost = total_hiring_needs * current_avg_salary * 12
    
    hiring_needs = {
        "assumed_attrition_rate": round(attrition_rate * 100, 1),
        "expected_annual_attrition": int(annual_attrition),
        "growth_hiring_needs": int(moderate_growth),
        "total_hiring_needs": int(total_hiring_needs),
        "estimated_hiring_cost": round(estimated_hiring_cost, 2)
    }
    
    # Monthly projection for next 12 months (Moderate 5% Growth)
    monthly_projection = []
    current_hc = current_headcount
    current_pay = current_monthly_payroll
    monthly_growth = (1.05) ** (1/12)  # Monthly growth rate to achieve 5% annual
    
    for month in range(1, 13):
        current_hc = int(current_hc * monthly_growth)
        current_pay = current_pay * monthly_growth
        monthly_projection.append({
            "month": f"Month {month}",
            "month_number": month,
            "projected_headcount": int(current_hc),
            "projected_monthly_payroll": round(current_pay, 2),
            "projected_annual_payroll_runrate": round(current_pay * 12, 2)
        })
    
    # Prepare chart data for LLM to recreate charts
    chart_data = {
        "scenario_headcount": {
            "scenarios": [s["scenario_name"] for s in scenarios],
            "current_headcount": [s["current_headcount"] for s in scenarios],
            "projected_headcount": [s["projected_headcount"] for s in scenarios],
            "chart_type": "bar",
            "title": "Headcount Projection by Scenario",
            "xlabel": "Scenario",
            "ylabel": "Headcount",
            "legend": ["Current", "Projected"]
        },
        "scenario_payroll": {
            "scenarios": [s["scenario_name"] for s in scenarios],
            "current_annual_payroll": [s["current_annual_payroll"] / 1e6 for s in scenarios],  # In millions
            "projected_annual_payroll": [s["projected_annual_payroll"] / 1e6 for s in scenarios],  # In millions
            "chart_type": "bar",
            "title": "Annual Payroll Projection by Scenario",
            "xlabel": "Scenario",
            "ylabel": "Annual Payroll (Millions USD)",
            "legend": ["Current", "Projected"]
        },
        "monthly_headcount": {
            "months": [m["month"] for m in monthly_projection],
            "month_numbers": [m["month_number"] for m in monthly_projection],
            "projected_headcount": [m["projected_headcount"] for m in monthly_projection],
            "baseline_headcount": current_headcount,
            "chart_type": "line",
            "title": "Monthly Headcount Projection (5% Growth)",
            "xlabel": "Month",
            "ylabel": "Headcount",
            "marker": "o"
        },
        "monthly_payroll": {
            "months": [m["month"] for m in monthly_projection],
            "month_numbers": [m["month_number"] for m in monthly_projection],
            "projected_monthly_payroll": [m["projected_monthly_payroll"] / 1e3 for m in monthly_projection],  # In thousands
            "baseline_monthly_payroll": current_monthly_payroll / 1e3,  # In thousands
            "chart_type": "line",
            "title": "Monthly Payroll Projection (5% Growth)",
            "xlabel": "Month",
            "ylabel": "Monthly Payroll (Thousands USD)",
            "marker": "s"
        }
    }
    
    # Generate human-readable summary
    summary_parts = [f"Workforce forecasting analysis for current workforce of {current_headcount} employees."]
    summary_parts.append(f"Current monthly payroll: ${current_monthly_payroll:,.2f}.")
    summary_parts.append(f"Current annual payroll: ${current_annual_payroll:,.2f}.")
    summary_parts.append(f"Average monthly salary: ${current_avg_salary:,.2f}.")
    
    if scenarios:
        moderate_scenario = next((s for s in scenarios if "Moderate" in s["scenario_name"]), None)
        if moderate_scenario:
            summary_parts.append(
                f"Moderate growth scenario (5%): Projected headcount {moderate_scenario['projected_headcount']} "
                f"(+{moderate_scenario['headcount_change']}), "
                f"projected annual payroll ${moderate_scenario['projected_annual_payroll']:,.2f} "
                f"(+${moderate_scenario['payroll_increase']:,.2f})."
            )
    
    summary_parts.append(
        f"Hiring needs (5% growth + 5% attrition): {total_hiring_needs} employees, "
        f"estimated cost ${estimated_hiring_cost:,.2f}."
    )
    
    summary_text = " ".join(summary_parts)
    
    return {
        "scenarios": scenarios,
        "department_forecast": department_forecast,
        "monthly_projection": monthly_projection,
        "hiring_needs": hiring_needs,
        "chart_data": chart_data,
        "summary": {
            "current_headcount": int(current_headcount),
            "current_monthly_payroll": round(current_monthly_payroll, 2),
            "current_annual_payroll": round(current_annual_payroll, 2),
            "average_monthly_salary": round(current_avg_salary, 2),
            "currency": "USD"
        },
        "summary_text": summary_text
    }

