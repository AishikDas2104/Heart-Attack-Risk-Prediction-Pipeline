from datetime import datetime, timedelta
from pathlib import Path
import shutil

from airflow import DAG
from airflow.operators.python import PythonOperator

# ---------- CONFIG ----------
DAG_DIR = Path(__file__).parent
RAW_DIR = DAG_DIR / "data" / "raw_data"
GOOD_DIR = DAG_DIR / "data" / "good_data"
# ----------------------------

def move_csv_files(**kwargs):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    GOOD_DIR.mkdir(parents=True, exist_ok=True)

    moved = []
    for f in RAW_DIR.glob("*.csv"):
        dest = GOOD_DIR / f.name
        shutil.move(str(f), str(dest))
        moved.append(f.name)

    if moved:
        print("Moved:", moved)
    else:
        print("No CSV files found in", RAW_DIR)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="move_csv_from_raw_to_good",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule=None,          # <- updated: use `schedule` instead of deprecated `schedule_interval`
    catchup=False,
    tags=["file-move"],
) as dag:

    move_files = PythonOperator(
        task_id="move_csv_files",
        python_callable=move_csv_files,
    )

    move_files
