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

def move_one_csv(**kwargs):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    GOOD_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(RAW_DIR.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in", RAW_DIR)
        return

    f = csv_files[0]  # move only the first file
    dest = GOOD_DIR / f.name
    shutil.move(str(f), str(dest))
    print(f"Moved: {f.name}")

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
    schedule=None,
    catchup=False,
    tags=["file-move"],
) as dag:

    move_file = PythonOperator(
        task_id="move_one_csv",
        python_callable=move_one_csv,
    )
