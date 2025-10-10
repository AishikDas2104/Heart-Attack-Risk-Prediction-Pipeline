# /opt/airflow/dags/dag2.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any
import pandas as pd
import requests
from airflow import DAG
from airflow.decorators import task
from airflow.exceptions import AirflowSkipException

# -------------------- Config / Paths --------------------
# Use paths relative to the DAG file so the code works inside the container.

DAG_DIR = Path(__file__).parent
RAW_DIR = DAG_DIR / "data" / "raw_data"
GOOD_DIR = DAG_DIR / "data" / "good_data"

# Try to create the predictions directory but do NOT fail import if there's an error.
logger = logging.getLogger("airflow.task")
# try:
#     PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
# except Exception as e:
#     logger.warning(
#         "Could not create PREDICTIONS_DIR at import time (%s). Continuing; tasks will attempt to create when running.",
#         e,
#     )

# -------------------- DAG Definition --------------------
with DAG(
    dag_id="check_new_data_and_predict",
    start_date=datetime(2025, 1, 1),
    schedule=timedelta(minutes=5),
    catchup=False,
    tags=["example", "safe-import"],
) as dag:


    @task(task_id="check_for_new_data")
    def check_for_new_data() -> List[Dict[str, Any]]:
       

        if not GOOD_DIR.exists():
            raise AirflowSkipException("good_data folder not found - skipping DAG run.")

        csv_files = sorted([p for p in GOOD_DIR.glob("*.csv") if p.is_file()])

        if not csv_files:
            raise AirflowSkipException("No CSV files in good_data - skipping DAG run.")

        logger.info("Found CSV files: %s", [str(p) for p in csv_files])

        first_rows: List[Dict[str, Any]] = []

        for csv_path in csv_files:
            try:
                df = pd.read_csv(csv_path)
                if df.empty:
                    logger.warning("CSV is empty: %s", csv_path)
                    continue

                # Convert the first row to a dictionary
                first_row_dict = df.iloc[0].to_dict()
                first_row_dict["__file_path__"] = str(csv_path.resolve())  # optional metadata
                first_rows.append(first_row_dict)

            except Exception as e:
                logger.error("Error reading %s: %s", csv_path, e)

        if not first_rows:
            raise AirflowSkipException("No valid data rows found in CSV files.")

        logger.info("Collected first rows from %d CSVs", first_rows)
        # first_rows[0]['Age']
        body_api  = {
            "Age": first_rows[0]['Age'],
            "Cholesterol": first_rows[0]['Cholesterol'],
            "Heart_rate": first_rows[0]['Heart rate'],
            "Diabetes": first_rows[0]['Diabetes'],
            "Smoking": first_rows[0]['Family History'],
            "Obesity": first_rows[0]['Obesity'],
            "Alcohol_Consumption": first_rows[0]['Alcohol Consumption'],
            "Exercise_Hours_Per_Week": first_rows[0]['Exercise Hours Per Week'],
            "Previous_Heart_Problems": first_rows[0]['Previous Heart Problems'],
            "Medication_Use": first_rows[0]['Medication Use'],
            "Stress_Level": first_rows[0]['Stress Level'],
            "Sedentary_Hours_Per_Day": first_rows[0]['Sedentary Hours Per Day'],
            "Income": first_rows[0]['Income'],
            "BMI": first_rows[0]['BMI'],
            "Triglycerides": first_rows[0]['Triglycerides'],
            "Physical_Activity_Days_Per_Week": first_rows[0]['Physical Activity Days Per Week'],
            "Sleep_Hours_Per_Day": first_rows[0]['Sleep Hours Per Day'],
            "Blood_sugar": first_rows[0]['Blood sugar'],
            "CK_MB": first_rows[0]['CK-MB'],
            "Troponin": first_rows[0]['Troponin']
        }
        # logger.info("Collected first rows from %d CSVs", body_api)

        url = "http://127.0.0.1:8000/predict"
        try:
            response =  requests.post(url, json=body_api)

            logger.info("API Response [%d]: %s", response.status_code, response.text)
            return {
                "status": "success",
                "api_status": response.status_code,
                "api_response": response.json(),
            }
        except Exception as e:
            logger.error("Error calling API: %s", e, )
            return {"status": "failed", "error": str(e)}
        return body


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
