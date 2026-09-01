# de-data-engineer

AWS CDK project that provisions a serverless data engineering platform on AWS. Apache Airflow (MWAA) orchestrates AWS Glue ETL jobs, with infrastructure deployed automatically through a CodePipeline CI/CD pipeline.

---

## Architecture

```
CodeCommit ──► CodePipeline ──► CodeBuild (cdk deploy)
                                      │
                    ┌─────────────────┼──────────────────┐
                    │                 │                  │
               StorageStack      IamStack           GlueStack
               (S3 buckets)    (IAM roles)       (Glue ETL job)
                    │                                    │
               MwaaStack ──────────────────────────────►│
            (MWAA / Airflow)   triggers via DAG          │
                    └────────────────────────────────────┘
```

### Stacks

| Stack | Resources |
|---|---|
| **StorageStack** | S3 bucket for MWAA DAGs, S3 bucket for Glue scripts |
| **IamStack** | Glue execution role, MWAA execution role with least-privilege policies |
| **GlueStack** | Uploads scripts to S3, creates the Glue ETL job with CloudWatch logging and job bookmarks |
| **MwaaStack** | Dedicated VPC (public + private subnets, NAT gateways), MWAA security group (self-referencing), MWAA environment v2.10.3 with full CloudWatch logging |
| **PipelineStack** | CodeCommit repo reference, CodeBuild project, CodePipeline (Source → Build) |

---

## Prerequisites

- AWS CLI configured with credentials for account `165223369428` / region `us-east-1`
- Node.js ≥ 20 and Python ≥ 3.11
- AWS CDK CLI: `npm install -g aws-cdk`
- CDK bootstrap already run in the target account/region

---

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Deploy

```bash
# Synthesise CloudFormation templates
cdk synth

# Deploy all stacks
cdk deploy --all --require-approval never
```

Stacks are deployed in dependency order automatically. The pipeline stack is self-contained and will redeploy everything on every push to the `main` branch of the `de-data-engineer` CodeCommit repository.

---

## Project Layout

```
.
├── app.py                  # CDK app entry point
├── buildspec.yml           # CodeBuild build specification
├── requirements.txt        # CDK Python dependencies
├── dags/
│   └── de_ingestion.py     # Airflow DAG: triggers the Glue ingestion job
├── glue/
│   └── Scripts/
│       └── ingestion_job.py  # AWS Glue PySpark ETL script
└── infra/
    ├── storage_stack.py    # S3 buckets
    ├── iam_stack.py        # IAM roles and policies
    ├── glue_stack.py       # Glue job
    ├── mwaa_stack.py       # MWAA environment
    └── pipeline_stack.py   # CI/CD pipeline
```

---

## DAG: de_ingestion

The `de_ingestion` DAG is triggered manually (no schedule). It runs two tasks in sequence:

1. **trigger_glue_job** — starts the `de-data-engineer-example-job` Glue job via `GlueJobOperator`
2. **wait_for_glue_job** — polls the job run every 60 seconds via `GlueJobSensor` until it succeeds or times out (1 hour)

The DAG uses the `aws_default` Airflow connection, which is pre-configured in MWAA to use the environment's execution role.

---

## Glue Job: ingestion_job.py

A PySpark / AWS Glue 4.0 ETL job. Job bookmarking is enabled so incremental loads only process new data. Metrics and continuous CloudWatch logging are on by default. Spark UI event logs are written to `s3://<glue-bucket>/spark-logs/`.

---

## CI/CD

Every push to the `main` branch of the CodeCommit repository triggers the pipeline:

1. **Source** — pulls the latest commit
2. **Build** — runs `cdk synth && cdk deploy --all` inside CodeBuild using the `buildspec.yml`

The CodeBuild role has `AdministratorAccess` so it can deploy all CDK stacks.
