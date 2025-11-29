from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any
import pandas as pd
import requests
import json
from airflow import DAG
from airflow.decorators import task
from airflow.exceptions import AirflowSkipException

# -------------------- Config / Paths --------------------
DAG_DIR = Path(__file__).parent
GOOD_DIR = DAG_DIR / "data" / "good_data"
PROCESSED_LOG = DAG_DIR / "data" / "processed_files.log"
API_URL = "http://host.docker.internal:8000/predict"

logger = logging.getLogger("airflow.task")

# -------------------- DAG Definition --------------------
with DAG(
    dag_id="prediction_job",
    start_date=datetime(2025, 1, 1),
    schedule=timedelta(minutes=2), # Run every 2 minutes
    catchup=False,
    tags=["prediction"],
) as dag:

    @task(task_id="check_for_new_data")
    def check_for_new_data() -> List[str]:
        if not GOOD_DIR.exists():
            raise AirflowSkipException("good_data folder not found - skipping DAG run.")

        # Get all CSV files
        all_files = sorted([p.name for p in GOOD_DIR.glob("*.csv") if p.is_file()])
        
        if not all_files:
            raise AirflowSkipException("No CSV files in good_data - skipping DAG run.")

        # Read processed files
        processed_files = set()
        if PROCESSED_LOG.exists():
            with open(PROCESSED_LOG, "r") as f:
                processed_files = set(line.strip() for line in f)

        # Filter new files
        new_files = [f for f in all_files if f not in processed_files]

        if not new_files:
            raise AirflowSkipException("No new files to process - skipping DAG run.")

        logger.info(f"Found {len(new_files)} new files: {new_files}")
        return new_files

    @task(task_id="make_predictions")
    def make_predictions(file_names: List[str]):
        if not file_names:
            return

        for file_name in file_names:
            file_path = GOOD_DIR / file_name
            logger.info(f"Processing {file_name}...")
            
            try:
                df = pd.read_csv(file_path)
                if df.empty:
                    logger.warning(f"File {file_name} is empty.")
                    continue

                # Prepare batch payload
                payload_list = []
                for _, row in df.iterrows():
                    payload_list.append({
                        "age": int(row.get("Age", row.get("age", 0))),
                        "gender": str(row.get("Gender", row.get("gender", "male"))).lower(),
                        "duration": float(row.get("Duration", row.get("duration", 0))),
                        "heart_rate": int(row.get("Heart_Rate", row.get("heart_rate", 0))),
                        "body_temp": float(row.get("Body_Temp", row.get("body_temp", 98.6)))
                    })
                
                # Call API
                response = requests.post(API_URL, params={"source": "scheduled"}, json=payload_list)
                response.raise_for_status()
                logger.info(f"Predictions successful for {file_name}")
                
                # Mark as processed
                with open(PROCESSED_LOG, "a") as f:
                    f.write(f"{file_name}\n")
                    
            except Exception as e:
                logger.error(f"Error processing {file_name}: {e}")

    # Task dependencies
    new_files = check_for_new_data()
    make_predictions(new_files)
