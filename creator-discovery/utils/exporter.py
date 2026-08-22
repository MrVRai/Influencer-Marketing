import pandas as pd
import os
import datetime
from typing import List, Dict, Any, Optional

class DataExporter:
    """Export campaign rosters and creator data to CSV and Excel."""

    def __init__(self, export_dir: Optional[str] = None):
        """Initialize the exporter and ensure export directory exists."""
        if export_dir is None:
            self.export_dir = 'd:/Influencer Marketing/creator-discovery/exports/'
        else:
            self.export_dir = export_dir
            
        os.makedirs(self.export_dir, exist_ok=True)

    def _generate_filename(self, prefix: str, ext: str) -> str:
        """Helper to generate a timestamped filename."""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        return os.path.join(self.export_dir, f"{prefix}_{timestamp}.{ext}")

    def export_creators_csv(self, creators: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Export list of creator dicts to CSV. 
        Auto-generate filename with timestamp if not provided. 
        Returns filepath.
        """
        if not creators:
            raise ValueError("No creator data provided for export.")
            
        if not filename:
            filepath = self._generate_filename('creators', 'csv')
        else:
            filepath = os.path.join(self.export_dir, filename)

        df = pd.DataFrame(creators)
        df.to_csv(filepath, index=False, encoding='utf-8')
        return filepath

    def export_creators_excel(self, creators: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        """
        Export list of creator dicts to Excel (.xlsx) with formatting.
        Includes bold headers and auto-column-width. 
        Returns filepath.
        """
        if not creators:
            raise ValueError("No creator data provided for export.")
            
        if not filename:
            filepath = self._generate_filename('creators', 'xlsx')
        else:
            filepath = os.path.join(self.export_dir, filename)

        df = pd.DataFrame(creators)
        
        # Requires 'xlsxwriter' package to be installed
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Creators', index=False)
            worksheet = writer.sheets['Creators']
            workbook = writer.book
            
            # Format header
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'bg_color': '#D7E4BC',
                'border': 1
            })
            
            # Write headers with formatting and set auto-column-width
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
                # Compute width: max length of items in column or header name
                column_len = max(df[value].astype(str).map(len).max(), len(str(value))) + 2
                # Put an upper bound on column width to avoid overly wide columns
                worksheet.set_column(col_num, col_num, min(column_len, 50))
                
        return filepath

    def export_campaign_roster(self, campaign_name: str, creators: List[Dict[str, Any]], format: str = 'excel') -> str:
        """
        Export a campaign roster with specifically formatted columns:
        Name, Platform, Subscribers/Followers, Median Views, Engagement Rate,
        Content Language, Est. Rate (Low-High), Creator Score, Past Sponsors, Status, Notes.
        """
        if not creators:
            raise ValueError("No creator data provided for roster export.")

        roster_data = []
        for c in creators:
            # Build Est. Rate string
            cpm_low = c.get('estimated_cpm_low')
            cpm_high = c.get('estimated_cpm_high')
            est_rate = "N/A"
            if cpm_low is not None and cpm_high is not None:
                est_rate = f"${cpm_low} - ${cpm_high}"
            elif cpm_low is not None:
                est_rate = f"~${cpm_low}"

            extra = c.get('extra_data') or {}
            if isinstance(extra, str):
                import json
                try:
                    extra = json.loads(extra)
                except Exception:
                    extra = {}
            if not isinstance(extra, dict):
                extra = {}

            roster_data.append({
                'Name': c.get('name', 'N/A'),
                'Platform': c.get('platform', 'N/A'),
                'Handle/ID': c.get('platform_id', 'N/A'),
                'Subscribers/Followers': c.get('subscriber_count', 0),
                'Median Views': c.get('median_views', 0),
                'Engagement Rate (%)': c.get('engagement_rate', 0.0),
                'Content Language': c.get('content_language', 'N/A'),
                'Est. Rate (Low-High)': est_rate,
                'Creator Score': c.get('creator_score', 0.0),
                'Contact Email': extra.get('bio_email') or c.get('bio_email', 'N/A'),
                'Verified': 'Yes' if (extra.get('is_verified') or c.get('is_verified')) else 'No',
                'Bio Link': extra.get('external_url') or c.get('external_url', 'N/A'),
                'Past Sponsors': c.get('past_sponsors', ''),
                'Status': c.get('status', 'N/A'),
                'Notes': c.get('notes', '')
            })

        # Sanitize campaign name for filename
        safe_name = "".join([char if char.isalnum() else "_" for char in campaign_name])
        
        if format.lower() == 'csv':
            filename = f"roster_{safe_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            return self.export_creators_csv(roster_data, filename)
        elif format.lower() == 'excel':
            filename = f"roster_{safe_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            return self.export_creators_excel(roster_data, filename)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'csv' or 'excel'.")
