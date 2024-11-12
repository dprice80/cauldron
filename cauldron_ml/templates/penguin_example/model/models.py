from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import PolynomialFeatures, StandardScaler, OneHotEncoder
from sklearn.linear_model import LinearRegression
from google.cloud import aiplatform
from google.cloud.bigquery import Client
import pickle
import gcsfs
import pandas as pd
from matplotlib import pyplot as plt
import os


def load_penguin_data(project_id: str, prefix: str):
    """
    Load penguin data from BigQuery ML public dataset.

    Parameters:
    - project_id (str): Google Cloud project ID.
    - prefix (str): Prefix for BigQuery dataset.

    Returns:
    - X (DataFrame): Features dataframe containing penguin data.
    - y (Series): Target series containing penguin body mass in grams.
    
    This function queries the 'bigquery-public-data.ml_datasets.penguins' dataset
    from BigQuery ML using the provided project ID and prefix. It retrieves 
    information about penguin species, island, culmen length and depth, flipper 
    length, body mass, and sex. The body mass is set as the target variable.
    The function then drops any rows with missing values, separates the features
    (X) from the target variable (y), and returns them as a tuple.
    """

    client = Client(project=project_id)
    QUERY = """
    select  species,
            island,
            culmen_length_mm,
            culmen_depth_mm,
            flipper_length_mm,
            body_mass_g,
            sex
    from `bigquery-public-data.ml_datasets.penguins`
    """

    target = 'body_mass_g'

    df = client.query(QUERY).to_dataframe()
    print("Done")
    df.dropna(how = 'any', inplace = True)
    X = df.drop(target, axis = 1).copy()
    y = df[target].astype('float64')
    return X, y


def create_preprocessor(column_names: list, poly_features: bool = True):
    """
    Create a preprocessor for transforming penguin data.

    Parameters:
    - column_names (list): List of column names in the dataset.
    - poly_features (bool): Whether to include polynomial features (default=True).

    Returns:
    - preprocessor (ColumnTransformer): Preprocessing pipeline for transforming
      numeric and categorical features of penguin data.

    This function creates a preprocessing pipeline for transforming numeric and
    categorical features of penguin data. It takes a list of column names and
    a boolean flag indicating whether to include polynomial features. Numeric
    features include 'culmen_length_mm', 'culmen_depth_mm', and 'flipper_length_mm',
    while categorical features include 'species', 'island', and 'sex'. If
    poly_features is True, polynomial features up to degree 2 are added to
    numeric features, otherwise, only mean imputation and scaling are applied.
    Categorical features are one-hot encoded with handle_unknown="ignore" to
    handle unseen categories during transformation. The preprocessor is returned
    as a ColumnTransformer object.
    """
    
    numeric_features = ['culmen_length_mm','culmen_depth_mm','flipper_length_mm']
    categorical_features = ['species','island','sex']
    numeric_features_int = [column_names.index(x) for x in numeric_features]
    categorical_features_int = [column_names.index(x) for x in categorical_features]

    if poly_features:
        numeric_transformer = Pipeline(
            steps=[
                ("imputenans", SimpleImputer(strategy="mean")),
                ("poly", PolynomialFeatures(degree=2)),
                ("scaler", StandardScaler()),
            ]
        )
    else:
        numeric_transformer = Pipeline(
            steps=[
                ("imputenans", SimpleImputer(strategy="mean")),
                ("scaler", StandardScaler()),
            ]
        )
    categorical_transformer = Pipeline(
        steps=[("onehot", OneHotEncoder(handle_unknown="ignore"))]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features_int),
            ("cat", categorical_transformer, categorical_features_int),
        ]
    )
    return preprocessor


def create_sklearn_pipeline(column_names: list, skl_model=LinearRegression(), poly_features=False):
    """
    Create a scikit-learn pipeline for preprocessing and modeling.

    Parameters:
    - column_names (list): List of column names in the dataset.
    - skl_model: Scikit-learn model object (default=LinearRegression())
    - poly_features (bool): Whether to include polynomial features (default=False).

    Returns:
    - pipe (Pipeline): Scikit-learn pipeline for preprocessing and modeling.

    This function creates a scikit-learn pipeline for preprocessing and modeling
    using the provided column names, scikit-learn model, and polynomial features
    flag. It first creates a preprocessing pipeline using the create_preprocessor
    function with specified column names and polynomial features flag. Then, it
    constructs the main pipeline by combining the preprocessing pipeline with the
    specified scikit-learn model. The resulting pipeline is returned.
    """

    preprocessor = create_preprocessor(
        column_names=column_names, poly_features=poly_features
    )

    pipe = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", skl_model)])
    return pipe


def threshold_check(val1, val2):
    """
    Check if val1 is greater than or equal to val2.

    Parameters:
    - val1: First value to compare.
    - val2: Second value to compare.

    Returns:
    - cond (str): 'true' if val1 is greater than or equal to val2, 'false' otherwise.

    This function compares val1 with val2 and returns 'true' if val1 is greater than
    or equal to val2, and 'false' otherwise. The comparison result is returned as a
    string indicating the condition.
    """
    
    cond = "false"
    if val1 >= val2:
        cond = "true"
    else:
        cond = "false"
    return cond

def create_feature_importance(pipe):
    """
    Create a bar plot of feature importance from a scikit-learn pipeline.

    Parameters:
    - pipe: Scikit-learn pipeline containing a preprocessor and a classifier.

    Returns:
    - fig: Matplotlib figure object containing the bar plot.

    This function extracts feature importance from a scikit-learn pipeline and
    creates a bar plot to visualize the importance of each feature. It retrieves
    the feature names and coefficients from the pipeline's preprocessor and classifier
    steps, respectively. The feature names are cleaned by removing prefixes, and
    the feature importance is plotted as a bar plot with feature names on the x-axis
    and importance values on the y-axis. The function returns the matplotlib figure
    object containing the bar plot.
    """

    feature_names = pipe.named_steps['preprocessor'].get_feature_names_out().tolist()
    feature_names = [name.split('__')[1] for name in feature_names]
    importance = pipe.named_steps['classifier'].coef_ # This becomes a 2D array so need to select the first element in dataframe
    feature_importance_df = pd.DataFrame([feature_names,importance[0]]).T.rename(columns = {0:'feature',1:'importance'})
    print('DATAFRAME:',feature_importance_df)

    fig = plt.figure(figsize=(10, 6))
    plt.bar(feature_importance_df['feature'], feature_importance_df['importance'])
    plt.xticks(rotation=90)
    plt.xlabel('Feature')
    plt.ylabel('Importance')
    plt.title('Feature Importance')

    return fig 


def get_latest_model_from_gcp(pipeline_settings):
    """
    Load the latest model from Google Cloud Storage using AI Platform (Vertex AI).

    Parameters:
    - pipeline_settings (dict): Dictionary containing pipeline settings including
      'GCP_PROJECT_ID' and 'REGION'.
    - model_id (str): ID of the model in the Model Registry.

    Returns:
    - pipe: Scikit-learn pipeline object loaded from the latest model.

    This function initializes the AI Platform (Vertex AI) client with the specified
    project ID and region, then retrieves the latest version of the model from the
    Model Registry using the provided model ID from the json config. It loads the 
    model from the model's URI in Google Cloud Storage, which is obtained from the 
    latest model version. The loaded model is returned as a scikit-learn pipeline 
    object.
    """

    GCP_PROJECT_ID = pipeline_settings['GCP_PROJECT_ID']
    REGION = pipeline_settings['REGION']

    script_dir = os.path.dirname(os.path.realpath(__file__))
    json_path = os.path.join(script_dir, "config", "inputs.json")

    json_file = pd.read_json(json_path, orient='index')
    model_id = str(json_file.iloc[0][0])

    if model_id == "":
        raise ValueError("Model ID is empty. Please provide a valid model ID.")

    aiplatform.init(project=GCP_PROJECT_ID, location=REGION)

    model_registry = aiplatform.models.ModelRegistry(model=model_id)
    versions = model_registry.list_versions()
    latest_version = versions[-1]  
    model = aiplatform.Model(latest_version.model_resource_name)
    model_path = model.uri
    gcs_model_path = model_path.replace('gs://','') + 'model.pkl'

    gcs_file_system = gcsfs.GCSFileSystem(
        project = f"{GCP_PROJECT_ID}"
    )

    with gcs_file_system.open(gcs_model_path) as f:
        pipe = pickle.load(f)

    return pipe

def create_predictions(model):
    """
    Create predictions using the provided model.

    Parameters:
    - model: Trained model object capable of making predictions.

    Returns:
    - df (DataFrame): DataFrame containing predicted body mass for sample data.

    This function creates predictions for a sample dataset using the provided model.
    It takes a dictionary `sample_data_dict` containing sample data with features
    such as 'species', 'island', 'culmen_length_mm', 'culmen_depth_mm',
    'flipper_length_mm', and 'sex'. The sample data is converted into a DataFrame
    `df`, and predictions for the 'body_mass_g' feature are generated using the
    `predict` method of the provided model. The DataFrame with predicted body mass
    values is returned.
    """

    sample_data_dict = {
        'species':'Adelie Penguin (Pygoscelis adeliae)',
        'island':'Dream',
        'culmen_length_mm':40,
        'culmen_depth_mm':18,
        'flipper_length_mm':190,
        'sex':'FEMALE'
    }

    df = pd.DataFrame([sample_data_dict])

    df["body_mass_g"] = model.predict(df)

    return df
