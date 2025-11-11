import pandas as pd
from typing import Dict


def cloud_marketing_breakdown(dfs: Dict[str, pd.DataFrame], month: str) -> dict:
    """
    Generate cloud and marketing spend breakdown for a specific month.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
        month: Fiscal month (e.g., "2024-01")
    
    Returns:
        JSON-serializable dict with cloud and marketing breakdown
    """
    result = {
        "cloud_costs": [],
        "marketing_spend": [],
        "total_cloud": 0.0,
        "total_marketing": 0.0
    }
    
    # Cloud costs breakdown
    cloud_df = dfs.get("fact_it_cloud_costs", pd.DataFrame()).copy()
    if not cloud_df.empty:
        cloud_month = cloud_df[cloud_df['fiscal_month'] == month]
        
        if not cloud_month.empty:
            # Group by provider and service
            cloud_by_provider_service = cloud_month.groupby(
                ['provider', 'service', 'env'], as_index=False
            )['amount'].sum()
            
            # Group by provider
            cloud_by_provider = cloud_month.groupby('provider', as_index=False)['amount'].sum()
            cloud_by_provider.rename(columns={'amount': 'total'}, inplace=True)
            
            # Convert to records
            cloud_costs = cloud_by_provider_service.to_dict('records')
            
            # Convert types for JSON serialization
            for item in cloud_costs:
                for key, value in item.items():
                    if pd.isna(value):
                        item[key] = None
                    elif isinstance(value, (float, int)):
                        item[key] = float(value)
                    else:
                        item[key] = str(value)
            
            result["cloud_costs"] = cloud_costs
            result["total_cloud"] = float(cloud_month['amount'].sum())
    
    # Marketing spend breakdown
    marketing_df = dfs.get("fact_marketing_spend_detail", pd.DataFrame()).copy()
    if not marketing_df.empty:
        marketing_month = marketing_df[marketing_df['fiscal_month'] == month]
        
        if not marketing_month.empty:
            # Group by channel and campaign
            marketing_by_channel = marketing_month.groupby(
                ['channel', 'campaign_id'], as_index=False
            )['amount'].sum()
            
            # Group by channel
            marketing_by_channel_total = marketing_month.groupby('channel', as_index=False)['amount'].sum()
            marketing_by_channel_total.rename(columns={'amount': 'total'}, inplace=True)
            
            # Convert to records
            marketing_spend = marketing_by_channel.to_dict('records')
            
            # Convert types for JSON serialization
            for item in marketing_spend:
                for key, value in item.items():
                    if pd.isna(value):
                        item[key] = None
                    elif isinstance(value, (float, int)):
                        item[key] = float(value)
                    else:
                        item[key] = str(value)
            
            result["marketing_spend"] = marketing_spend
            result["total_marketing"] = float(marketing_month['amount'].sum())
    
    # Round totals
    result["total_cloud"] = round(result["total_cloud"], 2)
    result["total_marketing"] = round(result["total_marketing"], 2)
    
    return result

