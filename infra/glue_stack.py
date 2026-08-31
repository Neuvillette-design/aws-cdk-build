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
                s3deploy.Source.asset(
                    "glue/Scripts"
                )
            ],
            destination_bucket=glue_bucket,
            destination_key_prefix="jobs",
        )

        # ---------------------------------------------------------
        # Glue Job
        # ---------------------------------------------------------

        self.example_job = glue.CfnJob(
            self,
            "ExampleGlueJob",
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

            execution_property=(
                glue.CfnJob.ExecutionPropertyProperty(
                    max_concurrent_runs=1,
                )
            ),
        )