import json
import pathlib
import airflow
import requests
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from requests.exceptions import MissingSchema, ConnectionError

dag = DAG(
    dag_id="download_rocket_launches",
    start_date=airflow.utils.dates.days_ago(14),
    schedule_interval='@daily',
)

download_launches = BashOperator(
    task_id="download_launches",
    bash_command="curl -o /tmp/launches.json -L 'https://ll.thespacedevs.com/2.0.0/launch/upcoming'",
    dag=dag,
)

def _get_pictures():
    pathlib.Path("/tmp/images").mkdir(parents=True, exist_ok=True)
    
    with open("/tmp/launches.json") as f:
        launches = json.load(f)
        image_urls = [launch["image"] for launch in launches["results"]]
        for image_url in image_urls:
            try:
                response = requests.get(image_url)
                image_filename = image_url.split("/")[-1]
                target_file = f"/tmp/images/{image_filename}"
                with open(target_file, "wb") as file:
                    file.write(response.content)
                print(f"Downloaded {image_url} to {target_file}")
            except MissingSchema:
                print(f"{image_url} appears to be an invalid URL.")
            except ConnectionError:
                print(f"Could not connect to {image_url}.")

get_pictures = PythonOperator(
    task_id="get_pictures",
    python_callable=_get_pictures,
    dag=dag,
)

notify = BashOperator(
    task_id="notify",
    bash_command='echo "There are now $(ls /tmp/images/ | wc -l) images."',
    dag=dag,
)

download_launches >> get_pictures >> notify

# download_launches >> get_pictures >> notify j
# B Instantiate a DAG object; this is the starting point of any workflow.
# c The name of the DAG
# d The date at which the DAG should first start running
# e At what interval the DAG should run
# f Apply Bash to download the URL response with curl.
# g The name of the task
# h A Python function will parse the response and download all rocket pictures.
# i Call the Python function in the DAG with a PythonOperator.
# j Set the order of execution of tasks.
