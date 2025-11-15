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
                        item[key] = round(float(value), 2)
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
                        item[key] = round(float(value), 2)
                    else:
                        item[key] = str(value)
            
            result["marketing_spend"] = marketing_spend
            result["total_marketing"] = float(marketing_month['amount'].sum())
    
    # Round totals
    result["total_cloud"] = round(result["total_cloud"], 2)
    result["total_marketing"] = round(result["total_marketing"], 2)
    
    # Calculate summary statistics
    total_spend = result["total_cloud"] + result["total_marketing"]
    cloud_count = len(result["cloud_costs"])
    marketing_count = len(result["marketing_spend"])
    
    # Get top providers and channels
    cloud_by_provider_dict = {}
    for item in result["cloud_costs"]:
        provider = item.get('provider', 'Unknown')
        amount = item.get('amount', 0)
        cloud_by_provider_dict[provider] = cloud_by_provider_dict.get(provider, 0) + amount
    
    marketing_by_channel_dict = {}
    for item in result["marketing_spend"]:
        channel = item.get('channel', 'Unknown')
        amount = item.get('amount', 0)
        marketing_by_channel_dict[channel] = marketing_by_channel_dict.get(channel, 0) + amount
    
    top_provider = max(cloud_by_provider_dict.items(), key=lambda x: x[1]) if cloud_by_provider_dict else None
    top_channel = max(marketing_by_channel_dict.items(), key=lambda x: x[1]) if marketing_by_channel_dict else None
    
    # Generate human-readable summary
    summary_parts = []
    summary_parts.append(f"Cloud and marketing breakdown for {month}.")
    
    if result["total_cloud"] > 0:
        summary_parts.append(f"Total cloud costs: ${result['total_cloud']:,.2f} across {cloud_count} service entries.")
        if top_provider:
            summary_parts.append(f"Top cloud provider: {top_provider[0]} with ${top_provider[1]:,.2f}.")
    else:
        summary_parts.append("No cloud costs recorded for this month.")
    
    if result["total_marketing"] > 0:
        summary_parts.append(f"Total marketing spend: ${result['total_marketing']:,.2f} across {marketing_count} campaign entries.")
        if top_channel:
            summary_parts.append(f"Top marketing channel: {top_channel[0]} with ${top_channel[1]:,.2f}.")
    else:
        summary_parts.append("No marketing spend recorded for this month.")
    
    if total_spend > 0:
        cloud_pct = (result["total_cloud"] / total_spend * 100) if total_spend > 0 else 0
        marketing_pct = (result["total_marketing"] / total_spend * 100) if total_spend > 0 else 0
        summary_parts.append(
            f"Total combined spend: ${total_spend:,.2f} "
            f"(Cloud: {cloud_pct:.1f}%, Marketing: {marketing_pct:.1f}%)."
        )
    
    summary_text = " ".join(summary_parts)
    
    return {
        "cloud_costs": result["cloud_costs"],
        "marketing_spend": result["marketing_spend"],
        "total_cloud": result["total_cloud"],
        "total_marketing": result["total_marketing"],
        "summary": {
            "month": month,
            "total_spend": round(total_spend, 2),
            "cloud_entries": cloud_count,
            "marketing_entries": marketing_count,
            "top_cloud_provider": top_provider[0] if top_provider else None,
            "top_cloud_provider_amount": round(top_provider[1], 2) if top_provider else 0.0,
            "top_marketing_channel": top_channel[0] if top_channel else None,
            "top_marketing_channel_amount": round(top_channel[1], 2) if top_channel else 0.0,
            "currency": "USD"
        },
        "summary_text": summary_text
    }

