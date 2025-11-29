"""
Export ingestion stats to CSV for Grafana
"""
import json
from pathlib import Path
import pandas as pd
from datetime import datetime

STATS_DIR = Path("airflow/dags/data/stats")
OUTPUT_FILE = "monitoring/ingestion_stats.csv"

def export_stats_to_csv():
    """Export all stats to CSV"""
    stats_data = []
    
    if STATS_DIR.exists():
        for file in STATS_DIR.glob("*.json"):
            with open(file) as f:
                data = json.load(f)
                stats_data.append({
                    'timestamp': data.get('timestamp'),
                    'filename': data.get('filename'),
                    'total_rows': data.get('total_rows', 0),
                    'valid_rows': data.get('valid_rows', 0),
                    'invalid_rows': data.get('invalid_rows', 0),
                    'num_issues': len(data.get('issues', []))
                })
    
    if stats_data:
        df = pd.DataFrame(stats_data)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"✅ Exported {len(stats_data)} records to {OUTPUT_FILE}")
        print(f"\nSummary:")
        print(f"Total files processed: {len(stats_data)}")
        print(f"Total rows: {df['total_rows'].sum()}")
        print(f"Valid rows: {df['valid_rows'].sum()}")
        print(f"Invalid rows: {df['invalid_rows'].sum()}")
    else:
        print("❌ No stats data found")

if __name__ == "__main__":
    export_stats_to_csv()
