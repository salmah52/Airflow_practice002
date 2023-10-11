import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from utils.db_ingestion import db_conn_ingestion

AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")

PG_HOST = os.getenv('PG_HOST')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_PORT = os.getenv('PG_PORT')
PG_DATABASE = os.getenv('PG_DATABASE')

URL_PREFIX = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow'

URL_TEMPLATE = URL_PREFIX + '/yellow_tripdata_{{ dag_run.logical_date.strftime(\'%Y-%m\') }}.csv.gz' # yellow_tripdata_2021-01.csv.gz
#https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz

OUTPUT_FILE_TEMPLATE = AIRFLOW_HOME + '/output_{{ dag_run.logical_date.strftime(\'%Y-%m\') }}.csv.gz'
#/opt/airflow/output_2021-01.csv.gz

TABLE_NAME_TEMPLATE = 'yellow_taxi_{{ dag_run.logical_date.strftime(\'%Y_%m\') }}'
#yellow_taxi_2021-01


DEFAULT_ARGS = {
    "owner": "airflow",
    "start_date": datetime(2021, 1, 1),
    "email": [os.getenv("ALERT_EMAIL", "")],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="LoadDataWebToDB9",
    description="Job to move data from website to local Postgresql DB",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 6 2 * *", # At 06:00 on day 2 of every month
    max_active_runs=1,
    catchup=True,
    tags=["Website_to_local_postgresql_DB"],
) as dag:

    start = EmptyOperator(task_id="start")

    download_file = BashOperator(
         task_id = "download_file",
         bash_command = f'curl -sSL {URL_TEMPLATE} > {OUTPUT_FILE_TEMPLATE}'
    )

    ingestion_data = PythonOperator(
        task_id ="ingestion_data",
        python_callable=db_conn_ingestion,
        op_kwargs=dict(
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT,
            db=PG_DATABASE,
            table_name=TABLE_NAME_TEMPLATE,
            csv_file=OUTPUT_FILE_TEMPLATE
        ),
    )

    delete_file = BashOperator(
         task_id = "delete_file",
         bash_command = f'rm {OUTPUT_FILE_TEMPLATE}'
    )

    end = EmptyOperator(task_id="end")

    start >> download_file >> ingestion_data >> delete_file >> end
