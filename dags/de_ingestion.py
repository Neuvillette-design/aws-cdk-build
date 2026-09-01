from datetime import datetime

from airflow import DAG
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.providers.amazon.aws.sensors.glue import GlueJobSensor

GLUE_JOB_NAME = "de-data-engineer-example-job"

with DAG(
    dag_id="de_ingestion",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["de", "ingestion", "glue"],
) as dag:

    # -------------------------------------------------------
    # Trigger the Glue ingestion job
    # -------------------------------------------------------

    trigger_glue_job = GlueJobOperator(
        task_id="trigger_glue_job",
        job_name=GLUE_JOB_NAME,
        script_args={},
        aws_conn_id="aws_default",
        region_name="us-east-1",
        wait_for_completion=False,
    )

    # -------------------------------------------------------
    # Wait for the Glue job to complete
    # -------------------------------------------------------

    wait_for_glue_job = GlueJobSensor(
        task_id="wait_for_glue_job",
        job_name=GLUE_JOB_NAME,
        run_id=trigger_glue_job.output,
        aws_conn_id="aws_default",
        poke_interval=60,
        timeout=3600,
    )

    trigger_glue_job >> wait_for_glue_job
