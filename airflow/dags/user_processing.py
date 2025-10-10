
from airflow.sdk import dag, task
# from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.sdk.bases.sensor import PokeReturnValue
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
@dag
def user_processing():
    create_table = SQLExecuteQueryOperator(
        task_id = "create_table",
        conn_id = "postgres",
        sql = """ 
        CREATE TABLE IF NOT EXISTS users(
        id INT PRIMARY KEY,
        firstname VARCHAR(255),
        lastname VARCHAR(255),
        email VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    
    @task.sensor(poke_interval=30, timeout=300)
    def is_api_availiable()-> PokeReturnValue:
        import requests
        response = requests.get("https://dummyuser.vercel.app/users")
        print(response.status_code)
        if response.status_code == 200:
            condition = True
            fake_user = response.json()
        else:
            condition = False
            fake_user = None
        return PokeReturnValue(is_done = condition, xcom_value=fake_user)
    
    @task
    def extract_user(fake_user):
        return {
            "id": fake_user["user"]["userid"],
            "firstname": fake_user["first_name"],
            "lastname": fake_user["last_name"],
            "email": fake_user["email"],
        }

    @task
    def process_user(user_info):
        import csv
        from datetime import datetime
        user_info = {
            "id": "23",
            "firstname": "kunjan",
            "lastname": "Rajbhandari",
            "email": "Kunjan@gmail.com",
        }
        user_info["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("/tmp/user_info.csv","w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames = user_info.keys())
            writer.writeheader()
            writer.writerow(user_info)

    @task
    def store_user():
        hook = PostgresHook(postgres_conn_id = "postgres")
        hook.copy_expert(
            sql = "COPY users FROM STDIN WITH CSV HEADER",
            filename= "/tmp/users1_info.csv"
        )
    process_user(extract_user(create_table >> is_api_availiable())) >> store_user()


    # fake_user = is_api_availiable()
    # user_info = extract_user(fake_user)
    # process_user(user_info)
    # store_user()
    
user_processing()   
