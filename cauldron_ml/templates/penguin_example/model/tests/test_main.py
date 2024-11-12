import pytest
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
import sys 
import os
from sklearn.utils import Bunch

script_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

from models import (
    load_penguin_data, 
    create_preprocessor, 
    create_sklearn_pipeline, 
    threshold_check, 
    create_feature_importance, 
    get_latest_model_from_gcp, 
    create_predictions
)

from utils.vertex import initialise_pipeline

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

# Region defaults to europe-west2. Don't change unless you have a good reason
REGION = pipeline_settings['REGION']

# DISPLAY NAME is made up of the user prefix and the project id
# e.g. f"{USER_PREFIX}-pipeline-{PROJECT_NAME}"
DISPLAY_NAME = pipeline_settings['DISPLAY_NAME']


@pytest.fixture
def penguin_data():
    return load_penguin_data(project_id=GCP_PROJECT_ID, prefix=USER_PREFIX)


@pytest.fixture
def preprocessor():
    column_names = ['species', 'island', 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'sex']
    return create_preprocessor(column_names)


@pytest.fixture
def pipeline():
    column_names = ['species', 'island', 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'sex']
    return create_sklearn_pipeline(column_names)


@pytest.fixture
def mock_model():
    class MockModel:
        def predict(self, df):
            return np.zeros(len(df))
    return MockModel()


def test_load_penguin_data(penguin_data):
    X, y = penguin_data
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert not X.isnull().values.any()
    assert not y.isnull().values.any()


def test_create_preprocessor(preprocessor):
    assert isinstance(preprocessor, ColumnTransformer)


def test_create_sklearn_pipeline(pipeline):
    assert isinstance(pipeline, Pipeline)


def test_threshold_check():
    assert threshold_check(5, 3) == 'true'
    assert threshold_check(3, 5) == 'false'
    assert threshold_check(5, 5) == 'true'


def test_create_feature_importance():
    class MockPipeline:
        @property
        def named_steps(self):
            return Bunch(preprocessor=MockPreprocessor(), classifier=MockClassifier())

    class MockPreprocessor:
        def get_feature_names_out(self):
            return np.array(['num__culmen_length_mm', 'num__culmen_depth_mm', 'num__flipper_length_mm'])
    
    class MockClassifier:
        def __init__(self):
            self.coef_ = [[0.5, 0.3, -0.1]]

    pipe = MockPipeline()
    fig = create_feature_importance(pipe)
    assert fig is not None


def test_get_latest_model_from_gcp():
    pipe = get_latest_model_from_gcp(pipeline_settings)
    assert pipe is not None


def test_create_predictions(mock_model):
    df = create_predictions(mock_model)
    assert isinstance(df, pd.DataFrame)
    assert 'body_mass_g' in df.columns
