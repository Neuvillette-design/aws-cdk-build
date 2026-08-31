#!/usr/bin/env python3

import os
import aws_cdk as cdk

from infra.storage_stack import StorageStack
from infra.iam_stack import IamStack
from infra.glue_stack import GlueStack
from infra.mwaa_stack import MwaaStack
from infra.pipeline_stack import PipelineStack


app = cdk.App()


# =========================================================
# AWS Environment
# =========================================================

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION"),
)


# =========================================================
# Storage
# =========================================================

storage_stack = StorageStack(
    app,
    "StorageStack",
    env=env,
)


# =========================================================
# IAM
# =========================================================

iam_stack = IamStack(
    app,
    "IamStack",
    env=env,
)


# =========================================================
# Glue
# =========================================================

glue_stack = GlueStack(
    app,
    "GlueStack",
    glue_bucket=storage_stack.glue_bucket,
    glue_role=iam_stack.glue_role,
    env=env,
)


# =========================================================
# MWAA
# =========================================================

mwaa_stack = MwaaStack(
    app,
    "MwaaStack",
    mwaa_bucket=storage_stack.mwaa_bucket,
    mwaa_role=iam_stack.mwaa_role,
    env=env,
)

pipeline_stack = PipelineStack(
    app,
    "PipelineStack",
    env=env,
)

app.synth()