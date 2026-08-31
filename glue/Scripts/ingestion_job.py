import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions

from pyspark.context import SparkContext


args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME"],
)

sc = SparkContext()
glue_context = GlueContext(sc)

job = Job(glue_context)

job.init(
    args["JOB_NAME"],
    args,
)

print("Hello from AWS Glue!")

job.commit()