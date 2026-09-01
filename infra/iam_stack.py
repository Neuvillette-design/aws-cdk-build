from aws_cdk import (
    Stack,
    aws_iam as iam,
)
from constructs import Construct


class IamStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:

        super().__init__(
            scope,
            construct_id,
            **kwargs,
        )

        # =========================================================
        # Glue execution role
        # =========================================================

        self.glue_role = iam.Role(
            self,
            "GlueExecutionRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSGlueServiceRole"
                )
            ],
        )

        # =========================================================
        # MWAA execution role
        # =========================================================

        self.mwaa_role = iam.Role(
            self,
            "MwaaExecutionRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("airflow.amazonaws.com"),
                iam.ServicePrincipal("airflow-env.amazonaws.com"),
            ),
        )

        # ---------------------------------------------------------
        # CloudWatch Logs
        # ---------------------------------------------------------

        self.mwaa_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogStream",
                    "logs:CreateLogGroup",
                    "logs:PutLogEvents",
                    "logs:GetLogEvents",
                    "logs:GetLogRecord",
                    "logs:GetLogGroupFields",
                    "logs:GetQueryResults",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams",
                ],
                resources=["*"],
            )
        )

        # ---------------------------------------------------------
        # S3 — account-level public access block check (required)
        # ---------------------------------------------------------

        self.mwaa_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetAccountPublicAccessBlock",
                ],
                resources=["*"],
            )
        )

        # ---------------------------------------------------------
        # Glue — Airflow triggers Glue jobs
        # ---------------------------------------------------------

        self.mwaa_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "glue:StartJobRun",
                    "glue:GetJobRun",
                    "glue:GetJobRuns",
                    "glue:BatchStopJobRun",
                    "glue:GetJob",
                    "glue:GetJobs",
                ],
                resources=["*"],
            )
        )

        # ---------------------------------------------------------
        # MWAA service API (allows environment to call back into
        # the MWAA control plane, e.g. CreateWebLoginToken)
        # ---------------------------------------------------------

        self.mwaa_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "airflow:PublishMetrics",
                    "airflow:CreateWebLoginToken",
                ],
                resources=["*"],
            )
        )

        # ---------------------------------------------------------
        # SSM — required for MWAA environment startup
        # ---------------------------------------------------------

        self.mwaa_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ssm:GetParameter",
                ],
                resources=["*"],
            )
        )

        # ---------------------------------------------------------
        # SQS — MWAA uses SQS internally for task queuing
        # ---------------------------------------------------------

        self.mwaa_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "sqs:ChangeMessageVisibility",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes",
                    "sqs:GetQueueUrl",
                    "sqs:ReceiveMessage",
                    "sqs:SendMessage",
                ],
                resources=[
                    f"arn:aws:sqs:{self.region}:*:airflow-celery-*"
                ],
            )
        )

        # ---------------------------------------------------------
        # KMS — for SQS / CloudWatch encryption used by MWAA
        # ---------------------------------------------------------

        self.mwaa_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "kms:Decrypt",
                    "kms:DescribeKey",
                    "kms:GenerateDataKey*",
                    "kms:Encrypt",
                ],
                not_resources=[
                    f"arn:aws:kms:*:{self.account}:key/*"
                ],
                conditions={
                    "StringLike": {
                        "kms:ViaService": [
                            f"sqs.{self.region}.amazonaws.com",
                        ]
                    }
                },
            )
        )
