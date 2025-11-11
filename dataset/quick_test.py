#!/usr/bin/env python3
"""
Quick test script to run individual analytics functions.

Usage:
    python quick_test.py runway
    python quick_test.py variance --quarter Q1 --version BUDGET_2024
    python quick_test.py burn
    python quick_test.py cloud_marketing --month 2024-01
    python quick_test.py slides --month 2024-01
"""

import sys
import json
import argparse
from load_data import load_all_tables
from analytics.runway import calculate_runway
from analytics.variance import variance_report
from analytics.burn import burn_by_function
from analytics.cloud_marketing import cloud_marketing_breakdown
from analytics.slides import generate_kpi_slide


def main():
    parser = argparse.ArgumentParser(description="Quick test for analytics functions")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Runway
    runway_parser = subparsers.add_parser("runway", help="Calculate cash runway")
    runway_parser.add_argument("--delay", type=int, default=0, help="CapEx delay in days")
    
    # Variance
    variance_parser = subparsers.add_parser("variance", help="Generate variance report")
    variance_parser.add_argument("--quarter", type=str, required=True, help="Fiscal quarter (e.g., Q1)")
    variance_parser.add_argument("--version", type=str, required=True, help="Budget version (e.g., BUDGET_2024)")
    
    # Burn
    burn_parser = subparsers.add_parser("burn", help="Calculate burn by function")
    
    # Cloud Marketing
    cloud_parser = subparsers.add_parser("cloud_marketing", help="Cloud and marketing breakdown")
    cloud_parser.add_argument("--month", type=str, required=True, help="Fiscal month (e.g., 2024-01)")
    
    # Slides
    slides_parser = subparsers.add_parser("slides", help="Generate KPI slide")
    slides_parser.add_argument("--month", type=str, required=True, help="Fiscal month (e.g., 2024-01)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Load data
    print("Loading data...")
    dfs = load_all_tables()
    print(f"Loaded {len(dfs)} tables\n")
    
    # Execute command
    try:
        if args.command == "runway":
            result = calculate_runway(dfs, delay_capex_days=args.delay)
            print(json.dumps(result, indent=2))
        
        elif args.command == "variance":
            result = variance_report(dfs, fiscal_quarter=args.quarter, budget_version=args.version)
            print(json.dumps(result, indent=2))
        
        elif args.command == "burn":
            result = burn_by_function(dfs)
            print(json.dumps(result, indent=2))
        
        elif args.command == "cloud_marketing":
            result = cloud_marketing_breakdown(dfs, month=args.month)
            print(json.dumps(result, indent=2))
        
        elif args.command == "slides":
            result = generate_kpi_slide(dfs, month=args.month)
            print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


