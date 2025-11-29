from datetime import datetime, timedelta
from pathlib import Path
import shutil
import random
import pandas as pd
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator

# ---------- CONFIG ----------
DAG_DIR = Path(__file__).parent
RAW_DIR = DAG_DIR / "data" / "raw_data"
GOOD_DIR = DAG_DIR / "data" / "good_data"
BAD_DIR = DAG_DIR / "data" / "bad_data"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
GOOD_DIR.mkdir(parents=True, exist_ok=True)
BAD_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("airflow.task")

def read_data(**kwargs):
    csv_files = sorted(list(RAW_DIR.glob("*.csv")))
    if not csv_files:
        logger.info("No CSV files found in %s", RAW_DIR)
        return None

    # Pick one randomly
    selected_file = random.choice(csv_files)
    logger.info(f"Selected file: {selected_file}")
    return str(selected_file)

def validate_data(file_path, **kwargs):
    # Handle both None and string 'None' from XCom
    if not file_path or file_path == 'None':
        return None

    df = pd.read_csv(file_path)
    issues = []
    
    # 1. Missing Columns
    required_columns = ["Age", "Gender", "Max_BPM", "Session_Duration (hours)", "BMI"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        issues.append({
            "type": "Missing Column",
            "column": ", ".join(missing_cols),
            "criticality": "High",
            "count": len(df)
        })

    # 2. Missing Values
    for col in df.columns:
        n_missing = df[col].isnull().sum()
        if n_missing > 0:
            issues.append({
                "type": "Missing Values",
                "column": col,
                "criticality": "Medium",
                "count": int(n_missing)
            })

    # 3. Unknown Categorical Values
    if "Gender" in df.columns:
        valid_genders = ["Male", "Female"]
        invalid_gender = df[~df["Gender"].isin(valid_genders) & df["Gender"].notnull()]
        if not invalid_gender.empty:
             issues.append({
                "type": "Unknown Value",
                "column": "Gender",
                "criticality": "Medium",
                "count": len(invalid_gender)
            })

    # 4. Out of Range
    if "Age" in df.columns:
        invalid_age = df[(df["Age"] <= 0) | (df["Age"] > 120)]
        if not invalid_age.empty:
            issues.append({
                "type": "Out of Range",
                "column": "Age",
                "criticality": "High",
                "count": len(invalid_age)
            })
            
    if "Max_BPM" in df.columns:
         invalid_bpm = df[(df["Max_BPM"] <= 0) | (df["Max_BPM"] > 250)]
         if not invalid_bpm.empty:
            issues.append({
                "type": "Out of Range",
                "column": "Max_BPM",
                "criticality": "High",
                "count": len(invalid_bpm)
            })

    # 5. Type Mismatch
    numeric_cols = ["Age", "Max_BPM", "Avg_BPM", "Session_Duration (hours)", "BMI"]
    for col in numeric_cols:
        if col in df.columns and df[col].dtype == 'object':
             n_invalid = pd.to_numeric(df[col], errors='coerce').isnull().sum()
             if n_invalid > 0:
                 issues.append({
                    "type": "Type Mismatch",
                    "column": col,
                    "criticality": "High",
                    "count": int(n_invalid)
                })

    return {
        "file_path": file_path,
        "total_rows": len(df),
        "issues": issues
    }

def save_statistics(ti, **kwargs):
    """Save ingestion statistics to PostgreSQL database"""
    validation_result = ti.xcom_pull(task_ids='validate_data')
    if not validation_result:
        return

    file_path = validation_result["file_path"]
    total_rows = validation_result["total_rows"]
    issues = validation_result["issues"]
    
    # Calculate valid/invalid rows
    invalid_rows_est = sum([i["count"] for i in issues])
    invalid_rows = min(invalid_rows_est, total_rows)
    valid_rows = total_rows - invalid_rows

    # Save to PostgreSQL database
    from sqlalchemy import create_engine, text
    
    # Connect to Airflow's PostgreSQL
    engine = create_engine("postgresql://airflow:airflow@postgres:5432/airflow")
    
    # Use begin() for automatic transaction management
    with engine.begin() as conn:
        # Insert ingestion stats
        result = conn.execute(
            text("""
                INSERT INTO ingestion_stats (timestamp, filename, total_rows, valid_rows, invalid_rows)
                VALUES (:timestamp, :filename, :total_rows, :valid_rows, :invalid_rows)
                RETURNING id
            """),
            {
                "timestamp": datetime.now(),
                "filename": Path(file_path).name,
                "total_rows": total_rows,
                "valid_rows": valid_rows,
                "invalid_rows": invalid_rows
            }
        )
        
        ingestion_id = result.scalar()
        
        # Insert data quality issues
        for issue in issues:
            conn.execute(
                text("""
                    INSERT INTO data_quality_issues 
                    (ingestion_stat_id, issue_type, column_name, criticality, count)
                    VALUES (:ingestion_id, :issue_type, :column_name, :criticality, :count)
                """),
                {
                    "ingestion_id": ingestion_id,
                    "issue_type": issue["type"],
                    "column_name": issue["column"],
                    "criticality": issue["criticality"],
                    "count": issue["count"]
                }
            )
        # Transaction auto-commits when exiting the with block
    
    logger.info(f"✅ Saved statistics to database for {Path(file_path).name}")

def send_alerts(ti, **kwargs):
    validation_result = ti.xcom_pull(task_ids='validate_data')
    if not validation_result:
        return

    issues = validation_result["issues"]
    if not issues:
        logger.info("No data quality issues found.")
        return

    # Mock Alert
    logger.warning("🚨 DATA QUALITY ALERT 🚨")
    for issue in issues:
        logger.warning(f"- {issue['criticality']} Severity: {issue['type']} in {issue['column']} ({issue['count']} rows)")

def split_and_save_data(ti, **kwargs):
    validation_result = ti.xcom_pull(task_ids='validate_data')
    if not validation_result:
        return

    file_path = Path(validation_result["file_path"])
    issues = validation_result["issues"]
    
    has_high_severity = any(i["criticality"] == "High" for i in issues)
    
    if has_high_severity:
        shutil.move(str(file_path), str(BAD_DIR / file_path.name))
        logger.info(f"Moved {file_path.name} to BAD_DATA")
    else:
        shutil.move(str(file_path), str(GOOD_DIR / file_path.name))
        logger.info(f"Moved {file_path.name} to GOOD_DATA")


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="data_ingestion_job",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule=timedelta(minutes=1),
    catchup=False,
    tags=["ingestion"],
) as dag:

    task_read = PythonOperator(
        task_id="read_data",
        python_callable=read_data,
    )

    task_validate = PythonOperator(
        task_id="validate_data",
        python_callable=validate_data,
        op_kwargs={"file_path": "{{ ti.xcom_pull(task_ids='read_data') }}"}
    )

    task_save_stats = PythonOperator(
        task_id="save_statistics",
        python_callable=save_statistics,
    )

    task_alert = PythonOperator(
        task_id="send_alerts",
        python_callable=send_alerts,
    )

    task_split = PythonOperator(
        task_id="split_and_save_data",
        python_callable=split_and_save_data,
    )

    task_read >> task_validate
    task_validate >> [task_save_stats, task_alert, task_split]
