from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_mwaa as mwaa,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
)
from constructs import Construct


class MwaaStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        mwaa_bucket,
        mwaa_role,
        **kwargs,
    ) -> None:

        super().__init__(
            scope,
            construct_id,
            **kwargs,
        )

        # =========================================================
        # MWAA DAG deployment
        # =========================================================

        dag_deployment = s3deploy.BucketDeployment(
            self,
            "DagsDeployment",
            sources=[
                s3deploy.Source.asset("dags")
            ],
            destination_bucket=mwaa_bucket,
            destination_key_prefix="dags",
        )

        # =========================================================
        # Grant MWAA role access to the MWAA S3 bucket
        # MWAA requires GetObject, GetBucketLocation, and ListBucket
        # on both the bucket and its objects.
        # =========================================================

        mwaa_bucket.grant_read(mwaa_role)

        mwaa_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetBucketLocation",
                    "s3:ListAllMyBuckets",
                ],
                resources=["*"],
            )
        )

        # =========================================================
        # Dedicated MWAA VPC
        # =========================================================

        mwaa_vpc = ec2.Vpc(
            self,
            "MwaaVpc",
            max_azs=2,
            nat_gateways=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="MwaaPublic",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="MwaaPrivate",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # =========================================================
        # MWAA Security Group
        # MWAA requires a self-referencing inbound rule so that
        # the scheduler, workers, and web server can communicate.
        # =========================================================

        mwaa_security_group = ec2.SecurityGroup(
            self,
            "MwaaSecurityGroup",
            vpc=mwaa_vpc,
            description="Security group for MWAA environment",
            allow_all_outbound=True,
        )

        # Self-referencing rule — all traffic within the SG
        mwaa_security_group.add_ingress_rule(
            peer=ec2.Peer.security_group_id(
                mwaa_security_group.security_group_id
            ),
            connection=ec2.Port.all_traffic(),
            description="Allow all inbound traffic from within the MWAA security group",
        )

        # =========================================================
        # MWAA Environment
        # =========================================================

        self.mwaa_environment = mwaa.CfnEnvironment(
            self,
            "MwaaEnvironment",
            name="de-data-engineer-mwaa",
            airflow_version="2.10.3",
            environment_class="mw1.small",
            execution_role_arn=mwaa_role.role_arn,
            source_bucket_arn=mwaa_bucket.bucket_arn,
            dag_s3_path="dags",
            network_configuration=mwaa.CfnEnvironment.NetworkConfigurationProperty(
                security_group_ids=[
                    mwaa_security_group.security_group_id
                ],
                subnet_ids=[
                    subnet.subnet_id
                    for subnet in mwaa_vpc.private_subnets[:2]
                ],
            ),
            min_workers=1,
            max_workers=2,
            schedulers=2,
            webserver_access_mode="PRIVATE_ONLY",

            # ---------------------------------------------------------
            # Logging configuration
            # All log groups ship to CloudWatch at INFO level.
            # ---------------------------------------------------------
            logging_configuration=mwaa.CfnEnvironment.LoggingConfigurationProperty(
                dag_processing_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                    enabled=True,
                    log_level="INFO",
                ),
                scheduler_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                    enabled=True,
                    log_level="INFO",
                ),
                task_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                    enabled=True,
                    log_level="INFO",
                ),
                webserver_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                    enabled=True,
                    log_level="INFO",
                ),
                worker_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                    enabled=True,
                    log_level="INFO",
                ),
            ),
        )

        # =========================================================
        # Dependencies
        # =========================================================

        self.mwaa_environment.node.add_dependency(dag_deployment)
