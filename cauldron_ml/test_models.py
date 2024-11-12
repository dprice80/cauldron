from unittest.mock import MagicMock
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline

from model.models import (
    load_penguin_data,
    create_preprocessor,
    create_sklearn_pipeline,
    threshold_check,
    create_feature_importance,
    get_latest_model_from_gcp,
    create_predictions
)


def test_load_penguin_data(mocker):
    # Mock the BigQuery client and its methods
    mock_client = mocker.patch('models.Client')
    mock_query = mock_client.return_value.query.return_value
    mock_query.to_dataframe.return_value = pd.DataFrame({
        'species': ['Adelie', 'Chinstrap'],
        'island': ['Dream', 'Biscoe'],
        'culmen_length_mm': [39.1, 48.7],
        'culmen_depth_mm': [18.7, 17.4],
        'flipper_length_mm': [181, 195],
        'body_mass_g': [3750, 3800],
        'sex': ['MALE', 'FEMALE']
    })

    X, y = load_penguin_data('dummy_project', 'dummy_prefix')
    assert X.shape == (2, 6)
    assert y.shape == (2,)
    assert 'body_mass_g' not in X.columns


def test_create_preprocessor():
    column_names = ['species', 'island', 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'sex']
    preprocessor = create_preprocessor(column_names, poly_features=False)
    assert isinstance(preprocessor, ColumnTransformer)


def test_create_sklearn_pipeline():
    column_names = ['species', 'island', 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'sex']
    pipeline = create_sklearn_pipeline(column_names)
    assert isinstance(pipeline, Pipeline)


def test_threshold_check():
    assert threshold_check(5, 3) == 'true'
    assert threshold_check(2, 3) == 'false'


def test_create_feature_importance(mocker):
    column_names = ['species', 'island', 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'sex']
    model = LinearRegression()
    pipeline = create_sklearn_pipeline(column_names, skl_model=model)
    pipeline.named_steps['classifier'].coef_ = np.array([1, 2, 3, 4, 5, 6])
    mock_plt = mocker.patch('models.plt')
    fig = create_feature_importance(pipeline)
    assert mock_plt.figure.called
    assert fig is not None


def test_get_latest_model_from_gcp(mocker):
    mock_read_json = mocker.patch('models.pd.read_json')
    mock_read_json.return_value = pd.DataFrame([['dummy_model_id']])
    mock_model = MagicMock()
    mock_model.uri = 'gs://dummy_bucket/dummy_model_path/'
    mock_ai_platform = mocker.patch('models.aiplatform')
    mock_ai_platform.models.ModelRegistry.return_value.list_versions.return_value = [mock_model]
    mock_ai_platform.Model.return_value = mock_model
    mock_gcs_file_system = mocker.patch('models.gcsfs.GCSFileSystem').return_value
    mock_gcs_file_system.open.return_value.__enter__.return_value = MagicMock()

    pipeline_settings = {'GCP_PROJECT_ID': 'dummy_project', 'REGION': 'dummy_region'}
    pipe = get_latest_model_from_gcp(pipeline_settings)
    assert pipe is not None


def test_create_predictions():
    model = MagicMock()
    model.predict.return_value = [4000]
    df = create_predictions(model)
    assert df['body_mass_g'].iloc[0] == 4000