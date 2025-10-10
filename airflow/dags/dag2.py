# /opt/airflow/dags/dag2.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Any

import pandas as pd

from airflow import DAG
from airflow.decorators import task
from airflow.exceptions import AirflowSkipException

# -------------------- Config / Paths --------------------
# Use paths relative to the DAG file so the code works inside the container.
DAG_DIR = Path(__file__).parent.resolve()
GOOD_DIR = DAG_DIR / "data" / "good_data"
PREDICTIONS_DIR = DAG_DIR / "data" / "predictions"

# Try to create the predictions directory but do NOT fail import if there's an error.
logger = logging.getLogger("airflow.task")
try:
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.warning(
        "Could not create PREDICTIONS_DIR at import time (%s). Continuing; tasks will attempt to create when running.",
        e,
    )

# -------------------- DAG Definition --------------------
with DAG(
    dag_id="check_new_data_and_predict",
    description="Check for CSVs in data/good_data and create a first-row prediction file",
    start_date=datetime(2025, 1, 1),
    schedule=None,  # no automatic schedule; use "@daily" if desired
    catchup=False,
    tags=["example", "safe-import"],
) as dag:

    @task(task_id="check_for_new_data")
    def check_for_new_data() -> List[str]:
        """Return a list of absolute CSV file paths found in GOOD_DIR.
        If folder missing or no CSVs, raise AirflowSkipException to gracefully skip the DAG run.
        """
        log = logging.getLogger("airflow.task.check_for_new_data")
        log.info("Checking for CSV files in: %s", GOOD_DIR)

        # Make sure GOOD_DIR exists — if not, skip (do not crash DAG parsing).
        if not GOOD_DIR.exists():
            log.warning("GOOD_DIR does not exist: %s", GOOD_DIR)
            raise AirflowSkipException("good_data folder not found - skipping DAG run.")

        # find CSV files (non-recursive) and return sorted absolute paths
        csv_files = sorted([str(p.resolve()) for p in GOOD_DIR.glob("*.csv") if p.is_file()])
        if not csv_files:
            log.info("No CSV files found in %s - skipping DAG run.", GOOD_DIR)
            raise AirflowSkipException("No CSV files in good_data - skipping DAG run.")

        log.info("Found %d CSV file(s). First: %s", len(csv_files), csv_files[0])
        return csv_files

    @task(task_id="make_predictions")
    def make_predictions(file_list: List[str]) -> Dict[str, Any]:
        log = logging.getLogger("airflow.task.make_predictions")
        summary: Dict[str, Any] = {"processed_file": None, "status": "failed", "first_row": None}

        # Fallback: if upstream didn't provide file_list (e.g. you ran this task alone),
        # try to discover files directly from GOOD_DIR.
        if not file_list:
            log.warning("No file_list received via XCom. Falling back to scanning GOOD_DIR: %s", GOOD_DIR)
            if not GOOD_DIR.exists():
                log.error("GOOD_DIR does not exist: %s", GOOD_DIR)
                summary["status"] = "no_input"
                return summary
            file_list = sorted([str(p.resolve()) for p in GOOD_DIR.glob("*.csv") if p.is_file()])

        if not file_list:
            log.error("No CSV files found after fallback scan.")
            summary["status"] = "no_input"
            return summary

        first_file = file_list[0]
        summary["processed_file"] = first_file
        log.info("Processing file: %s", first_file)

        try:
            PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log.warning("Could not ensure PREDICTIONS_DIR exists at runtime: %s", e)

        try:
            df = pd.read_csv(first_file)
        except FileNotFoundError:
            log.exception("File not found at runtime: %s", first_file)
            summary["status"] = "file_not_found"
            return summary
        except Exception as exc:
            log.exception("Error reading CSV %s: %s", first_file, exc)
            summary["status"] = "read_error"
            summary["error"] = str(exc)
            return summary

        if df.empty:
            log.warning("CSV is empty: %s", first_file)
            summary["status"] = "empty_file"
            return summary

        try:
            first_row_series = df.iloc[0]
            first_row_dict = first_row_series.to_dict()
            out_path = PREDICTIONS_DIR / f"{Path(first_file).stem}_first_row.csv"
            pd.DataFrame([first_row_dict]).to_csv(out_path, index=False)
            log.info("Saved first row of %s to %s", Path(first_file).name, out_path)
            summary["status"] = "success"
            summary["first_row"] = first_row_dict
            summary["out_path"] = str(out_path.resolve())
            return summary
        except Exception as exc:
            log.exception("Error while processing/saving first row for %s: %s", first_file, exc)
            summary["status"] = "error"
            summary["error"] = str(exc)
            return summary

    # Task dependencies
    files = check_for_new_data()
    make_predictions(files)
