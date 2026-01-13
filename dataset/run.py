#!/usr/bin/env python3
"""
Local test runner for analytics functions.
"""
import argparse
import json
import pandas as pd
from load_data import load_all_tables
from analytics.runway import calculate_runway
from analytics.variance import variance_report
from analytics.burn import burn_by_function
from analytics.cloud_marketing import cloud_marketing_breakdown
from analytics.slides import generate_kpi_slide


def main():
    parser = argparse.ArgumentParser(description="Test analytics functions")
    subparsers = parser.add_subparsers(dest="command", help="Analytics function to run")
    
    # Runway command
    runway_parser = subparsers.add_parser("runway", help="Calculate cash runway")
    runway_parser.add_argument("--delay", type=int, default=0, help="CapEx delay in days")
    
    # Variance command
    variance_parser = subparsers.add_parser("variance", help="Generate variance report")
    variance_parser.add_argument("--month", type=str, required=True, help="Fiscal month (e.g., 2024-03)")
    variance_parser.add_argument("--version", type=str, required=True, help="Budget version (e.g., BUDGET_2024)")
    
    # Burn command
    burn_parser = subparsers.add_parser("burn", help="Calculate burn by function")
    
    # Cloud marketing command
    cloud_marketing_parser = subparsers.add_parser("cloud_marketing", help="Cloud and marketing breakdown")
    cloud_marketing_parser.add_argument("--month", type=str, required=True, help="Fiscal month (e.g., 2024-01)")
    
    # Slides command
    slides_parser = subparsers.add_parser("slides", help="Generate KPI slide")
    slides_parser.add_argument("--month", type=str, required=True, help="Fiscal month (e.g., 2024-01)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load data
    print("Loading data...")
    dfs = load_all_tables()
    print(f"Loaded {len(dfs)} tables\n")
    
    # Execute command
    if args.command == "runway":
        result = calculate_runway(dfs, delay_capex_days=args.delay)
        print("Cash Runway Analysis:")
        print(json.dumps(result, indent=2))
    
    elif args.command == "variance":
        # Derive quarter from month using dim_time
        dim_time_df = dfs.get("dim_time", pd.DataFrame())
        fiscal_quarter = None
        if not dim_time_df.empty:
            month_rows = dim_time_df[dim_time_df['fiscal_month'] == args.month]
            if not month_rows.empty:
                fiscal_quarter = month_rows.iloc[0]['fiscal_quarter']
        
        if not fiscal_quarter:
            print(f"Error: Could not determine fiscal quarter for month {args.month}")
            return
        
        result = variance_report(dfs, fiscal_quarter=fiscal_quarter, budget_version=args.version)
        print(f"Variance Report (Month: {args.month}, Quarter: {fiscal_quarter}, Version: {args.version}):")
        print(json.dumps(result, indent=2))
    
    elif args.command == "burn":
        result = burn_by_function(dfs)
        print("Burn by Function:")
        print(json.dumps(result, indent=2))
    
    elif args.command == "cloud_marketing":
        result = cloud_marketing_breakdown(dfs, month=args.month)
        print(f"Cloud & Marketing Breakdown (Month: {args.month}):")
        print(json.dumps(result, indent=2))
    
    elif args.command == "slides":
        result = generate_kpi_slide(dfs, month=args.month)
        print(f"KPI Slide (Month: {args.month}):")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

