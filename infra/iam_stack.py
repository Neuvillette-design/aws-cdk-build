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
            assumed_by=iam.ServicePrincipal(
                "glue.amazonaws.com"
            ),
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
                iam.ServicePrincipal(
                    "airflow.amazonaws.com"
                ),
                iam.ServicePrincipal(
                    "airflow-env.amazonaws.com"
                ),
            ),
        )

        # ---------------------------------------------------------
        # CloudWatch Logs permissions
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
        # S3 permissions
        # Bucket-specific permissions will be added from
        # the MWAA stack.
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
        # Glue permissions for Airflow -> Glue
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