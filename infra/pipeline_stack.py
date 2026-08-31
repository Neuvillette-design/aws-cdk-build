from aws_cdk import (
    Stack,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as pipeline_actions,
    aws_iam as iam
)
from constructs import Construct


class PipelineStack(Stack):

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
        # CodeCommit Repository
        # =========================================================

        repository = codecommit.Repository.from_repository_name(
            self,
            "DataEngineerRepository",
            repository_name="de-data-engineer",
        )

        # =========================================================
        # CodeBuild
        # =========================================================

        build_project = codebuild.PipelineProject(
            self,
            "CdkBuildProject",

            project_name="de-data-engineer-cdk-build",

            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
                privileged=False,
            ),

            build_spec=codebuild.BuildSpec.from_source_filename(
                "buildspec.yml"
            ),
        )

        build_project.role.add_managed_policy(
        iam.ManagedPolicy.from_aws_managed_policy_name(
        "AdministratorAccess"
    )
)
        # =========================================================
        # CodePipeline Artifact
        # =========================================================

        source_output = codepipeline.Artifact(
            "SourceOutput"
        )

        build_output = codepipeline.Artifact(
            "BuildOutput"
        )

        # =========================================================
        # Pipeline
        # =========================================================

        pipeline = codepipeline.Pipeline(
    self,
    "DataEngineerPipeline",
    pipeline_name="de-data-engineer-pipeline",
    pipeline_type=codepipeline.PipelineType.V2,
    cross_account_keys=False,
)
        # =========================================================
        # Source Stage
        # =========================================================

        pipeline.add_stage(
            stage_name="Source",

            actions=[
                pipeline_actions.CodeCommitSourceAction(
                    action_name="CodeCommit",

                    repository=repository,

                    branch="main",

                    output=source_output,
                )
            ],
        )

        # =========================================================
        # Build Stage
        # =========================================================

        pipeline.add_stage(
            stage_name="Build",

            actions=[
                pipeline_actions.CodeBuildAction(
                    action_name="CDKBuild",

                    project=build_project,

                    input=source_output,

                    outputs=[
                        build_output
                    ],
                )
            ],
        )