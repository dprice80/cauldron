from google.cloud import aiplatform
import subprocess
import os
from dotenv import dotenv_values
from cauldron_ml.cli import read_profile_yaml, read_config_yaml, rename_docker_image


def get_active_project_id():
    """
    Retrieves the active project ID.

    If the 'CLOUD_ML_PROJECT_ID' environment variable is set, it returns the value of that variable.
    Otherwise, it makes a request to the Google metadata server to fetch the project ID.

    Returns:
        str: The active project ID. If the project ID is not found in the lookup table, it returns 'production-project-name' 
        key from .caulprofile.
    """

    profile = read_profile_yaml()

    if 'CLOUD_ML_PROJECT_ID' in os.environ:
        projectid = os.environ['CLOUD_ML_PROJECT_ID']
    else:
        result = subprocess.run(
            args=["curl", "-s", "http://metadata.google.internal/computeMetadata/v1/project/project-id",
                  "-H", "Metadata-Flavor: Google"],
            stdout=subprocess.PIPE
            )
        projectid = result.stdout.decode("utf-8").strip()

    # Project ID sometimes comes back as a numeric value. Need to convert this to
    # text string version to use consistently various places like service account.

    id_lookup = {
        profile['production-project-numeric-id']: profile['production-project-name'],
        profile['production-project-name']: profile['production-project-name'],
        profile['sandbox-project-name']: profile['sandbox-project-name'],
        profile['sandbox-project-numeric-id']: profile['sandbox-project-name'],
    }

    project = id_lookup.get(projectid, profile['production-project-name'])
    print(f"Project detected: {project} \nProject ID: {projectid}")
    return project


def get_user_prefix():
    profile = read_profile_yaml()
    if get_active_project_id() == profile['production-project-name']:
        return 'prod'

    return profile["user-prefix"]


def initialise_pipeline(region: str = "europe-west2"):
    # DEFINE SOME CONSTANTS
    # Extract variables from config. These come from the .env file in the repo root and are set during the 
    # "caul create" process
    config = read_config_yaml()

    pipeline_settings = {}
    # Set the GCP project ID where the pipeline will be executed
    # This will change automatically in prod
    pipeline_settings['GCP_PROJECT_ID'] = get_active_project_id()

    # User prefix will be used in several places to correctly name piplines in explore space. Important for keeping pipeline test-runs separate 
    # when more than one person is working on a project. This will be modified to "prod" when deployed into production.
    pipeline_settings['USER_PREFIX'] = get_user_prefix()

    # Set the pipeline root. All vertex outputs will be saved here
    pipeline_settings['GCP_BUCKET_ID'] = f"gs://{pipeline_settings['GCP_PROJECT_ID']}-vertex-pipeline-root/"

    # Location of the pipeline in GCS
    pipeline_settings['PIPELINE_ROOT'] = (f"{pipeline_settings['GCP_BUCKET_ID']}pipeline-{config['CAUL_PROJECT_NAME']}/")

    # Set the display name for vertex pipelines (will show as this name in the pipeline list in GCP console > vertex > pipelines)
    pipeline_settings['DISPLAY_NAME'] = f"{pipeline_settings['USER_PREFIX']}-pipeline-{config['CAUL_PROJECT_NAME']}"

    pipeline_settings['REGION'] = region

    if pipeline_settings['USER_PREFIX'] == "prod":
        pipeline_settings['SERVICE_ACCOUNT'] = "robot-scientist@msmg-datascience-prod.iam.gserviceaccount.com"
    else:
        pipeline_settings['SERVICE_ACCOUNT'] = "robot-scientist@msmg-datascience-explore.iam.gserviceaccount.com"

    pipeline_settings['PROJECT_NAME'] = config['CAUL_PROJECT_NAME']

    pipeline_settings['IMAGE_TAG'] = config['CAUL_PIPELINES_IMAGE_TAG']

    aiplatform.init(project=pipeline_settings['GCP_PROJECT_ID'], location=pipeline_settings['REGION'])

    return pipeline_settings

