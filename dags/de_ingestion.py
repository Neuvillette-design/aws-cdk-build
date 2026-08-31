from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator


def hello_world():
    print("Hello from MWAA!")


with DAG(
    dag_id="example_dag",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    task = PythonOperator(
        task_id="hello_world",
        python_callable=hello_world,
    )