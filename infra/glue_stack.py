from aws_cdk import (
    Stack,
    aws_glue as glue,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct


class GlueStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        glue_bucket,
        glue_role,
        **kwargs,
    ) -> None:

        super().__init__(
            scope,
            construct_id,
            **kwargs,
        )

        # ---------------------------------------------------------
        # Upload Glue scripts to S3
        # ---------------------------------------------------------

        s3deploy.BucketDeployment(
            self,
            "GlueScriptsDeployment",
            sources=[
                s3deploy.Source.asset("glue/Scripts")
            ],
            destination_bucket=glue_bucket,
            destination_key_prefix="jobs",
        )

        # ---------------------------------------------------------
        # Glue Job
        # ---------------------------------------------------------

        self.ingestion_job = glue.CfnJob(
            self,
            "IngestionGlueJob",
            name="de-data-engineer-example-job",
            role=glue_role.role_arn,

            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=(
                    f"s3://{glue_bucket.bucket_name}"
                    "/jobs/ingestion_job.py"
                ),
            ),

            glue_version="4.0",
            worker_type="G.1X",
            number_of_workers=2,

            execution_property=glue.CfnJob.ExecutionPropertyProperty(
                max_concurrent_runs=1,
            ),

            # ---------------------------------------------------------
            # Default arguments passed to every job run.
            # Individual runs can override these via script_args in
            # the GlueJobOperator.
            # ---------------------------------------------------------
            default_arguments={
                "--job-language": "python",
                "--job-bookmark-option": "job-bookmark-enable",
                "--enable-metrics": "true",
                "--enable-continuous-cloudwatch-log": "true",
                "--enable-spark-ui": "true",
                "--spark-event-logs-path": (
                    f"s3://{glue_bucket.bucket_name}/spark-logs/"
                ),
                "--TempDir": (
                    f"s3://{glue_bucket.bucket_name}/tmp/"
                ),
            },
        )
