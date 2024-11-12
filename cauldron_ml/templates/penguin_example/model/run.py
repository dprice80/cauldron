from components import load_data, train, evaluate, register_model
from kfp.dsl import pipeline, If
from kfp import compiler
from google.cloud.aiplatform import pipeline_jobs
from cauldron_ml.vertex import initialise_pipeline
from google.cloud import aiplatform

pipeline_settings = initialise_pipeline()

DISPLAY_NAME = pipeline_settings['DISPLAY_NAME']
GCP_PROJECT_ID = pipeline_settings['GCP_PROJECT_ID']
USER_PREFIX = pipeline_settings['USER_PREFIX']
GCP_BUCKET_ID = pipeline_settings['GCP_BUCKET_ID']
PIPELINE_ROOT = pipeline_settings['PIPELINE_ROOT']
REGION = pipeline_settings['REGION']
SERVICE_ACCOUNT = pipeline_settings['SERVICE_ACCOUNT']

aiplatform.init(project=GCP_PROJECT_ID, location=REGION)
 

@pipeline(
    # Default pipeline root. You can override it when submitting the pipeline.
    pipeline_root=PIPELINE_ROOT,
    # A name for the pipeline. Use to determine the pipeline Context.
    name=f"{DISPLAY_NAME}-pipeline"
)
def ml_pipeline(
    project: str = GCP_PROJECT_ID,
    region: str = REGION
):
    data_op = load_data()

    train_model_op = (
        train(
            x_train_dataset=data_op.outputs["x_train_dataset"],
            y_train_dataset=data_op.outputs["y_train_dataset"]
        )
        .set_cpu_limit('4')
        .set_memory_limit('32G')
    )

    model_evaluation_op = evaluate(
        x_test_dataset=data_op.outputs["x_test_dataset"],
        y_test_dataset=data_op.outputs["y_test_dataset"],
        model=train_model_op.outputs["model"],
        threshold=0.5
    )

    with If(
        model_evaluation_op.outputs["threshold_passed"] == "true",  # pylint: disable=no-member
        name=f"deploy-{DISPLAY_NAME}-pipe"
    ):
        register_model(
            model=train_model_op.outputs["model"],
            project=project,
            region=region
        )


compiler.Compiler().compile(
    # Here we are passing a function to be compiled, not evaluating a function
    pipeline_func=ml_pipeline,
    # The output directory
    package_path=f"{DISPLAY_NAME}-pipeline.json"
)


pipeline = pipeline_jobs.PipelineJob(
    display_name=DISPLAY_NAME,
    template_path=f"{DISPLAY_NAME}-pipeline.json",
    enable_caching=False,
    location=REGION
)

pipeline.run(service_account=SERVICE_ACCOUNT)
