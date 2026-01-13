import pandas as pd
from typing import Dict


def generate_kpi_slide(dfs: Dict[str, pd.DataFrame], month: str) -> dict:
    """
    Generate KPI summary and narrative for a specific month.
    
    Args:
        dfs: Dictionary of table name -> DataFrame
        month: Fiscal month (e.g., "2024-01")
    
    Returns:
        JSON-serializable dict with KPI values and narrative
    """
    result = {
        "month": month,
        "kpis": [],
        "narrative": "",
        "key_metrics": {}
    }
    
    # Load KPI tables
    kpi_monthly_df = dfs.get("kpi_monthly", pd.DataFrame())
    kpi_definitions_df = dfs.get("kpi_definitions", pd.DataFrame())
    metric_targets_df = dfs.get("metric_targets", pd.DataFrame())
    commentary_library_df = dfs.get("commentary_library", pd.DataFrame())
    
    # Get KPIs for the month
    if not kpi_monthly_df.empty:
        month_kpis = kpi_monthly_df[kpi_monthly_df['fiscal_month'] == month].copy()
        
        # Join with definitions
        if not kpi_definitions_df.empty:
            month_kpis = month_kpis.merge(
                kpi_definitions_df[['kpi_id', 'name', 'display_format', 'owner']],
                on='kpi_id',
                how='left'
            )
        
        # Join with targets
        if not metric_targets_df.empty:
            month_targets = metric_targets_df[metric_targets_df['fiscal_month'] == month]
            month_kpis = month_kpis.merge(
                month_targets[['kpi_id', 'target_value', 'traffic_light_thresholds']],
                on='kpi_id',
                how='left'
            )
        
        # Convert to records
        kpi_records = month_kpis.to_dict('records')
        
        # Convert types and build key metrics
        for kpi in kpi_records:
            kpi_name = kpi.get('name', f"KPI_{kpi.get('kpi_id', '')}")
            kpi_value = kpi.get('value', 0)
            target_value = kpi.get('target_value')
            
            # Convert types
            for key, value in kpi.items():
                if pd.isna(value):
                    kpi[key] = None
                elif isinstance(value, (float, int)):
                    kpi[key] = float(value)
                else:
                    kpi[key] = str(value) if value is not None else None
            
            # Add to key metrics
            result["key_metrics"][kpi_name] = {
                "value": kpi_value,
                "target": target_value,
                "status": "on_target"  # Could be enhanced with threshold logic
            }
            
            # Check status against thresholds if available
            thresholds = kpi.get('traffic_light_thresholds')
            if thresholds and target_value:
                try:
                    # Simple threshold check (could be enhanced)
                    variance_pct = ((kpi_value - target_value) / target_value) * 100 if target_value != 0 else 0
                    if abs(variance_pct) < 5:
                        kpi['status'] = 'on_target'
                    elif variance_pct > 0:
                        kpi['status'] = 'above_target'
                    else:
                        kpi['status'] = 'below_target'
                except:
                    kpi['status'] = 'unknown'
        
        result["kpis"] = kpi_records
    
    # Generate narrative from commentary library
    if not commentary_library_df.empty:
        # Get relevant commentary blocks (simplified - could be enhanced with topic matching)
        commentary_blocks = commentary_library_df.to_dict('records')
        narrative_parts = []
        
        for block in commentary_blocks:
            text = block.get('text_md', '')
            if text:
                narrative_parts.append(text)
        
        result["narrative"] = " ".join(narrative_parts) if narrative_parts else "No commentary available for this period."
    else:
        result["narrative"] = f"Financial summary for {month}. Key metrics tracked across operational and financial dimensions."
    
    return result

