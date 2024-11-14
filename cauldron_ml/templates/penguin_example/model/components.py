from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

from models import (
    load_penguin_data,
    create_sklearn_pipeline,
    threshold_check,
    create_feature_importance
)
from typing import NamedTuple


# These types are used as inputs to the various components. They are important for letting kubeflow know what it should pass to your
# functions (i.e. a model resource) and what it should return.
from kfp.dsl import (
    Dataset,
    Input,
    Model,
    Output,
    Metrics,
    component,
    Markdown
)

import pandas as pd
import pickle
from google.cloud import aiplatform
from cauldron_ml.vertex import initialise_pipeline
import os 

# Generate the pipeline settings and also initialise aiplatform
pipeline_settings = initialise_pipeline()

# Set the GCP project ID. Do not set this manually, it will change dynamically depending on there it is run.
GCP_PROJECT_ID = pipeline_settings['GCP_PROJECT_ID']

# User prefix will be used in several places to correctly name piplines in explore space. Important for keeping pipeline test-runs separate
# when more than one person is working on a project. This will be modified to "prod" when deployed into production.
USER_PREFIX = pipeline_settings['USER_PREFIX']

# Image tag will determine the name of the image built during the "caul build" step. This is a requirement of each @component instance below.
# Note that the image tag cannot vary between different components in the same pipeline.
IMAGE_TAG = pipeline_settings['IMAGE_TAG']

# Set the pipeline root. All vertex outputs will be saved here
GCP_BUCKET_ID = pipeline_settings['GCP_BUCKET_ID']

# Location of the pipeline in GCS
PIPELINE_ROOT = pipeline_settings['PIPELINE_ROOT']

# Region defaults to europe-west2
REGION = pipeline_settings['REGION']

# Wrap the load_data function in a @component decorator. Decorators basically take a function modify it's behaviour by wrapping it in some additional code
# and return another function or object in it's place. In this case load_data function will be transformed into a kubeflow component object, which has all sorts of
# functionality normal functions don't have. For example in the run.py file you will see that the function train gets the method .set_cpu_limit() after it has been
# wrapped with the component decorator. All components have this method, which allows you to set resource limits, and many others
# https://kubeflow-pipelines.readthedocs.io/en/master/source/dsl.html#kfp.dsl.PipelineTask


@component(target_image=IMAGE_TAG, output_component_file="load_data.yaml")
def load_data(
    # It might seem strange to have an Output as one of the inputs to a function. The reason for this is that kubeflow passes your function an Output object,
    # which is essentially some allocated resource for you to save your outputs to. x_train_dataset is therefore not actually a dataset, it's an object that can contain
    # all sorts of meta data/attributes/methods. The important thing here is the .path attribute which we use to save our data to disk for later use. This is helpful
    # when we want to use our data across several different components. When an Output is specified, kubeflow will create a NEW resource for you to save to. When an output
    # is defined, kubeflow needs to be passed that argument from another instantiated component in the run.py file (i.e. within a Pipeline).
    # NOTE: You may want to write a component to delete your data after the pipeline has completed successfully.
    x_train_dataset: Output[Dataset],
    x_test_dataset: Output[Dataset],
    y_train_dataset: Output[Dataset],
    y_test_dataset: Output[Dataset],
    random_state: int = 0
):
    """Load training data and perform the train/test split.

    Data is loaded in from the output step.

    Args:
        random_state: int = 0
            Random number generator seed
        x_train_dataset (Output[Dataset])
            An Output object is something passed by kubeflow when executing the pipeline defining a resource location and other metadata. To use it
            you can refer to the .path attribute of this object, adding your own file extension (e.g. x_train_dataset.path + ".feather")
        x_test_dataset (Output[Dataset]) 
            Same as above
        y_train_dataset (Output[Dataset])
            Same as above
        y_test_dataset (Output[Dataset])
            Same as above
    """

    # Within a component you can do pretty much anything you want. From this point on it's a standard python function
    X, y = load_penguin_data(project_id=GCP_PROJECT_ID, prefix=USER_PREFIX)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, random_state=random_state)
    # Note: must reset index when saving to feather. Don't forget to drop this when loading.
    # Also, y can only be saved to feather when it is a dataset. Dropping index creates a dataset
    # from y which must be dropped on load
    X_train.reset_index().to_feather(x_train_dataset.path + ".feather")
    X_test.reset_index().to_feather(x_test_dataset.path + ".feather")
    y_train.reset_index().to_feather(y_train_dataset.path + ".feather")
    y_test.reset_index().to_feather(y_test_dataset.path + ".feather")
    # This component does not need to return anything (see evaluate for an example of a returned variable)
    # return None

@component(target_image=IMAGE_TAG, output_component_file="train.yaml")
def train(
    # Inputs in this case are datasets that will come from the load_data step. There is a working example in the run.py file of how to use the output (saved data) of
    # load_data as an input to the train component.
    x_train_dataset: Input[Dataset],
    y_train_dataset: Input[Dataset],
    # Again, an output is defined. This time it is a model.
    model: Output[Model]
):
    X_train = pd.read_feather(
        x_train_dataset.path + ".feather").drop("index", axis = 1)
    y_train = pd.read_feather(
        y_train_dataset.path + ".feather").drop("index", axis = 1)
    pipe = create_sklearn_pipeline(
        column_names=X_train.columns.tolist(), skl_model=LinearRegression()
    )
    pipe.fit(X_train, y_train)

    # Meta data for the model can be recorded in the metadata attribute.
    model.metadata["framework"] = "LM"
    file_name = model.path + ".pkl"
    with open(file_name, "wb") as file:
        pickle.dump(pipe, file)


@component(target_image=IMAGE_TAG, output_component_file="evaluate.yaml")
def evaluate(
    x_test_dataset: Input[Dataset],
    y_test_dataset: Input[Dataset],
    model: Input[Model],
    # Here we have a normal function input. This may be used to pass
    threshold: float,
    metrics: Output[Metrics],
    markdown_artifact: Output[Markdown]
) -> NamedTuple("output", [("threshold_passed", str)]):

    X_test = pd.read_feather(x_test_dataset.path + ".feather").drop("index", axis = 1)
    y_test = pd.read_feather(y_test_dataset.path + ".feather").drop("index", axis = 1)

    with open(model.path + ".pkl", "rb") as file:
        pipe = pickle.load(file)

    r2 = pipe.score(X_test, y_test)
    metrics.log_metric("R-squared", r2)
    threshold_passed = threshold_check(r2, threshold)

    feature_importance_fig = create_feature_importance(pipe)

    # Markdown content
    bucket_path = markdown_artifact.path.replace('markdown_artifact.md', '')
    feature_importance_fig.savefig(bucket_path + 'evaluation_feature_importance_figure.png')
    markdown_content = f"""
    ![Seaborn Plot]({bucket_path + 'evaluation_feature_importance_figure.png'})
    """
    with open(markdown_artifact.path, 'w') as f:
        f.write(markdown_content)

    # We need to return a tuple with one item, this will be converted to a named tuple ("threshold_passed"="true")
    # (see output in function definition)
    return (threshold_passed,)


# In run.py there is some control flow logic preventing register_model from running if the output ['register_model'] is below a threshold
@component(target_image=IMAGE_TAG, output_component_file="register_model.yaml")
def register_model(model: Input[Model], project: str, region: str):

    print("DEBUG: Model URI", model.uri)

    script_dir = os.path.dirname(os.path.realpath(__file__))
    json_path = os.path.join(script_dir, "config", "inputs.json")

    json_file = pd.read_json(json_path, orient='index')
    model_id = str(json_file.iloc[0][0])

    # Note: serving_container_image_uri won't be used unless deploying via vertex.
    # However, it is still a required argument, so here we just use a random image.
    # It is not downloaded, but vertex checks to see if the image exists and is readable.
    # For retraining, set parent_model. You can get the ID from the Model Registry page in
    # vertex console. Click on the model, then the version and click on the version details tab
    # the model ID is a string of numbers (e.g. 4682107539163185134).
    if model_id == "":

        aiplatform.Model.upload(
            display_name=f"{USER_PREFIX}-penguin",
            artifact_uri=model.uri.replace("model", ""),
            #parent_model=str(model_id), # set this once a v1 has been trained.
            # not used but needed to upload model.
            serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest"
        )

    else:

        aiplatform.Model.upload(
            display_name=f"{USER_PREFIX}-penguin",
            artifact_uri=model.uri.replace("model", ""),
            parent_model=str(model_id), # set this once a v1 has been trained.
            # not used but needed to upload model.
            serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest"
        )
