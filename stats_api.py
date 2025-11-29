"""
Simple API to serve data quality stats for Grafana
"""
from fastapi import FastAPI
from pathlib import Path
import json
from typing import List
from datetime import datetime

app = FastAPI(title="Stats API for Grafana")

STATS_DIR = Path("airflow/dags/data/stats")

@app.get("/ingestion-stats")
def get_ingestion_stats() -> List[dict]:
    """Get all ingestion statistics"""
    stats = []
    if STATS_DIR.exists():
        for file in STATS_DIR.glob("*.json"):
            with open(file) as f:
                data = json.load(f)
                stats.append(data)
    return sorted(stats, key=lambda x: x.get("timestamp", ""))

@app.get("/ingestion-stats/summary")
def get_summary():
    """Get summary statistics"""
    stats = get_ingestion_stats()
    if not stats:
        return {"total_files": 0, "total_rows": 0}
    
    return {
        "total_files": len(stats),
        "total_rows": sum(s.get("total_rows", 0) for s in stats),
        "total_valid": sum(s.get("valid_rows", 0) for s in stats),
        "total_invalid": sum(s.get("invalid_rows", 0) for s in stats),
        "recent_stats": stats[-10:]  # Last 10
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
