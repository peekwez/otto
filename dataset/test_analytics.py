#!/usr/bin/env python3
"""
Comprehensive test script for financial analytics functions.

This script tests:
1. Database connectivity
2. Data loading
3. All analytics functions (runway, variance, burn, cloud_marketing, slides)
"""

import sys
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy import text

from load_data import load_all_tables, connect_engine
from analytics.runway import calculate_runway
from analytics.variance import variance_report
from analytics.burn import burn_by_function
from analytics.cloud_marketing import cloud_marketing_breakdown
from analytics.slides import generate_kpi_slide


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def test_database_connection() -> bool:
    """Test database connection."""
    print_header("Testing Database Connection")
    try:
        engine = connect_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print_success("Database connection successful")
        return True
    except Exception as e:
        print_error(f"Database connection failed: {str(e)}")
        return False


def test_data_loading() -> Optional[Dict[str, pd.DataFrame]]:
    """Test data loading from database."""
    print_header("Testing Data Loading")
    try:
        print_info("Loading all tables...")
        dfs = load_all_tables()
        
        if not dfs:
            print_error("No tables loaded")
            return None
        
        print_success(f"Loaded {len(dfs)} tables")
        
        # List all loaded tables
        print_info("Loaded tables:")
        for table_name in sorted(dfs.keys()):
            row_count = len(dfs[table_name])
            print(f"  - {table_name}: {row_count:,} rows")
        
        # Check for empty tables
        empty_tables = [name for name, df in dfs.items() if df.empty]
        if empty_tables:
            print_warning(f"Empty tables: {', '.join(empty_tables)}")
        
        return dfs
    except Exception as e:
        print_error(f"Data loading failed: {str(e)}")
        traceback.print_exc()
        return None


def get_available_months(dfs: Dict[str, pd.DataFrame]) -> list:
    """Get available fiscal months from dim_time."""
    try:
        dim_time = dfs.get("dim_time", pd.DataFrame())
        if dim_time.empty:
            return []
        
        if 'fiscal_month' in dim_time.columns:
            months = sorted(dim_time['fiscal_month'].dropna().unique().tolist())
            return months
        return []
    except Exception:
        return []


def get_available_quarters(dfs: Dict[str, pd.DataFrame]) -> list:
    """Get available fiscal quarters from dim_time."""
    try:
        dim_time = dfs.get("dim_time", pd.DataFrame())
        if dim_time.empty:
            return []
        
        if 'fiscal_quarter' in dim_time.columns:
            quarters = sorted(dim_time['fiscal_quarter'].dropna().unique().tolist())
            return quarters
        return []
    except Exception:
        return []


def get_available_budget_versions(dfs: Dict[str, pd.DataFrame]) -> list:
    """Get available budget versions from fact_budget_monthly."""
    try:
        budget_df = dfs.get("fact_budget_monthly", pd.DataFrame())
        if budget_df.empty:
            return []
        
        # Check for 'version' column (as used in variance.py)
        if 'version' in budget_df.columns:
            versions = sorted(budget_df['version'].dropna().unique().tolist())
            return versions
        # Also check for 'budget_version' as fallback
        elif 'budget_version' in budget_df.columns:
            versions = sorted(budget_df['budget_version'].dropna().unique().tolist())
            return versions
        return []
    except Exception:
        return []


def test_runway(dfs: Dict[str, pd.DataFrame]) -> bool:
    """Test runway calculation."""
    print_header("Testing Runway Calculation")
    try:
        print_info("Testing with delay=0 days...")
        result = calculate_runway(dfs, delay_capex_days=0)
        
        if not isinstance(result, dict):
            print_error("Result is not a dictionary")
            return False
        
        required_keys = ['current_cash', 'monthly_burn', 'runway_months', 'projection']
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            print_error(f"Missing keys in result: {missing_keys}")
            return False
        
        print_success("Runway calculation completed")
        print_info(f"Current cash: ${result['current_cash']:,.2f}")
        print_info(f"Monthly burn: ${result['monthly_burn']:,.2f}")
        print_info(f"Runway: {result['runway_months']:.2f} months")
        print_info(f"Projection months: {len(result['projection'])}")
        
        # Test with delay
        if result['projection']:
            print_info("Testing with delay=90 days...")
            result_delayed = calculate_runway(dfs, delay_capex_days=90)
            print_success("Runway calculation with delay completed")
        
        return True
    except Exception as e:
        print_error(f"Runway calculation failed: {str(e)}")
        traceback.print_exc()
        return False


def test_variance(dfs: Dict[str, pd.DataFrame]) -> bool:
    """Test variance report."""
    print_header("Testing Variance Report")
    try:
        # Get available quarters and budget versions
        quarters = get_available_quarters(dfs)
        versions = get_available_budget_versions(dfs)
        
        if not quarters:
            print_warning("No fiscal quarters available in data")
            return False
        
        if not versions:
            print_warning("No budget versions available in data")
            return False
        
        # Use first available quarter and version
        quarter = quarters[0]
        version = versions[0]
        
        print_info(f"Testing with quarter={quarter}, version={version}")
        result = variance_report(dfs, fiscal_quarter=quarter, budget_version=version)
        
        if not isinstance(result, dict):
            print_error("Result is not a dictionary")
            return False
        
        if 'rows' not in result:
            print_error("Missing 'rows' key in result")
            return False
        
        print_success("Variance report completed")
        print_info(f"Variance rows: {len(result['rows'])}")
        
        if result['rows']:
            # Show sample row
            sample = result['rows'][0]
            print_info(f"Sample row keys: {list(sample.keys())}")
        
        return True
    except Exception as e:
        print_error(f"Variance report failed: {str(e)}")
        traceback.print_exc()
        return False


def test_burn(dfs: Dict[str, pd.DataFrame]) -> bool:
    """Test burn by function."""
    print_header("Testing Burn by Function")
    try:
        result = burn_by_function(dfs)
        
        if not isinstance(result, dict):
            print_error("Result is not a dictionary")
            return False
        
        if 'functions' not in result:
            print_error("Missing 'functions' key in result")
            return False
        
        print_success("Burn by function completed")
        print_info(f"Functions analyzed: {len(result['functions'])}")
        
        if result['functions']:
            # Show summary
            for func in result['functions'][:5]:  # Show first 5
                print_info(f"  - {func.get('function', 'N/A')}: "
                          f"${func.get('avg_monthly_burn', 0):,.2f}/month")
        
        return True
    except Exception as e:
        print_error(f"Burn by function failed: {str(e)}")
        traceback.print_exc()
        return False


def test_cloud_marketing(dfs: Dict[str, pd.DataFrame]) -> bool:
    """Test cloud and marketing breakdown."""
    print_header("Testing Cloud & Marketing Breakdown")
    try:
        months = get_available_months(dfs)
        
        if not months:
            print_warning("No fiscal months available in data")
            return False
        
        # Use first available month
        month = months[0]
        
        print_info(f"Testing with month={month}")
        result = cloud_marketing_breakdown(dfs, month=month)
        
        if not isinstance(result, dict):
            print_error("Result is not a dictionary")
            return False
        
        required_keys = ['cloud_costs', 'marketing_spend', 'total_cloud', 'total_marketing']
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            print_error(f"Missing keys in result: {missing_keys}")
            return False
        
        print_success("Cloud & marketing breakdown completed")
        print_info(f"Total cloud: ${result['total_cloud']:,.2f}")
        print_info(f"Total marketing: ${result['total_marketing']:,.2f}")
        print_info(f"Cloud cost entries: {len(result['cloud_costs'])}")
        print_info(f"Marketing spend entries: {len(result['marketing_spend'])}")
        
        return True
    except Exception as e:
        print_error(f"Cloud & marketing breakdown failed: {str(e)}")
        traceback.print_exc()
        return False


def test_slides(dfs: Dict[str, pd.DataFrame]) -> bool:
    """Test KPI slide generation."""
    print_header("Testing KPI Slide Generation")
    try:
        months = get_available_months(dfs)
        
        if not months:
            print_warning("No fiscal months available in data")
            return False
        
        # Use first available month
        month = months[0]
        
        print_info(f"Testing with month={month}")
        result = generate_kpi_slide(dfs, month=month)
        
        if not isinstance(result, dict):
            print_error("Result is not a dictionary")
            return False
        
        required_keys = ['month', 'kpis', 'narrative', 'key_metrics']
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            print_error(f"Missing keys in result: {missing_keys}")
            return False
        
        print_success("KPI slide generation completed")
        print_info(f"Month: {result['month']}")
        print_info(f"KPIs: {len(result['kpis'])}")
        print_info(f"Narrative length: {len(result.get('narrative', ''))} characters")
        print_info(f"Key metrics: {len(result['key_metrics'])}")
        
        return True
    except Exception as e:
        print_error(f"KPI slide generation failed: {str(e)}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Financial Analytics Test Suite")
    parser.add_argument("--save-results", action="store_true", 
                       help="Save test results to JSON file")
    parser.add_argument("--output-dir", type=str, default="test_results",
                       help="Directory to save test results (default: test_results)")
    args = parser.parse_args()
    
    print_header("Financial Analytics Test Suite")
    print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    test_outputs = {}  # Store actual function outputs if saving
    
    # Test 1: Database connection
    results['database'] = test_database_connection()
    if not results['database']:
        print_error("\nCannot proceed without database connection. Please check your connection settings.")
        sys.exit(1)
    
    # Test 2: Data loading
    dfs = test_data_loading()
    if dfs is None:
        print_error("\nCannot proceed without data. Please check your database and schema.")
        sys.exit(1)
    
    results['data_loading'] = True
    
    # Test 3: Runway
    results['runway'] = test_runway(dfs)
    if args.save_results and results['runway']:
        try:
            test_outputs['runway'] = calculate_runway(dfs, delay_capex_days=0)
            test_outputs['runway_delayed'] = calculate_runway(dfs, delay_capex_days=90)
        except:
            pass
    
    # Test 4: Variance
    results['variance'] = test_variance(dfs)
    if args.save_results and results['variance']:
        try:
            quarters = get_available_quarters(dfs)
            versions = get_available_budget_versions(dfs)
            if quarters and versions:
                test_outputs['variance'] = variance_report(dfs, fiscal_quarter=quarters[0], budget_version=versions[0])
        except:
            pass
    
    # Test 5: Burn
    results['burn'] = test_burn(dfs)
    if args.save_results and results['burn']:
        try:
            test_outputs['burn'] = burn_by_function(dfs)
        except:
            pass
    
    # Test 6: Cloud & Marketing
    results['cloud_marketing'] = test_cloud_marketing(dfs)
    if args.save_results and results['cloud_marketing']:
        try:
            months = get_available_months(dfs)
            if months:
                test_outputs['cloud_marketing'] = cloud_marketing_breakdown(dfs, month=months[0])
        except:
            pass
    
    # Test 7: Slides
    results['slides'] = test_slides(dfs)
    if args.save_results and results['slides']:
        try:
            months = get_available_months(dfs)
            if months:
                test_outputs['slides'] = generate_kpi_slide(dfs, month=months[0])
        except:
            pass
    
    # Save results if requested
    if args.save_results:
        import os
        from pathlib import Path
        
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save test results summary
        summary = {
            "test_timestamp": timestamp,
            "test_results": results,
            "passed": sum(1 for v in results.values() if v),
            "total": len(results)
        }
        summary_path = output_dir / f"test_summary_{timestamp}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print_info(f"Test summary saved to: {summary_path}")
        
        # Save function outputs
        if test_outputs:
            outputs_path = output_dir / f"test_outputs_{timestamp}.json"
            with open(outputs_path, 'w') as f:
                json.dump(test_outputs, f, indent=2)
            print_info(f"Test outputs saved to: {outputs_path}")
    
    # Print summary
    print_header("Test Summary")
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        color = Colors.GREEN if passed else Colors.RED
        print(f"{color}{'✓' if passed else '✗'} {test_name}: {status}{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}Total: {passed_tests}/{total_tests} tests passed{Colors.RESET}")
    
    if failed_tests > 0:
        print_warning(f"{failed_tests} test(s) failed. Please review the errors above.")
        sys.exit(1)
    else:
        print_success("All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

