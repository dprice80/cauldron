import yaml
import os
from .exceptions import ConfigurationError


def write_config_yaml(
            caul_pipelines_root_path: str = None,
            caul_pipelines_image_repo: str = None, caul_pipelines_project_path: str = None,
            caul_project_name: str = None, caul_pipelines_image_tag: str = None, config: dict = None,
            caul_docker_base_image: str = None
        ):

    if config:
        pass
    else:
        config = {
            'CAUL_PIPELINES_DOCKER_BASE_IMAGE': caul_docker_base_image,
            'CAUL_PIPELINES_ROOT_PATH': caul_pipelines_root_path,
            'CAUL_PIPELINES_IMAGE_REPO': caul_pipelines_image_repo,
            'CAUL_PIPELINES_PROJECT_PATH': caul_pipelines_project_path,
            'CAUL_PROJECT_NAME': caul_project_name,
            'CAUL_PIPELINES_IMAGE_TAG': caul_pipelines_image_tag
        }

    root = os.getcwd()
    with open(f"{root}/.caulconf", "w") as f:
        yaml.dump(config, f)


def read_config_yaml(root: str = os.getcwd(), return_path: bool = False):
    """
    Reads a YAML configuration file named '.caulconf' from the specified root directory or any of its parent directories.
    Args:
        root (str): The root directory to start searching for the configuration file. Defaults to the current working directory.
        return_path (bool): If True, returns the path to the configuration file instead of its contents. Defaults to False.
    Returns:
        dict or str: The contents of the configuration file as a dictionary if return_path is False, otherwise the path to the configuration file.
    Raises:
        ConfigurationError: If no configuration file is found from the root directory up to the user's home directory.
    """
    
    current_dir = root
    while True:
        if current_dir == os.path.expanduser("~"):
            break  # Don't read from the user directory
        config_path = os.path.join(current_dir, '.caulconf')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            if return_path is False:
                return config
            else:
                return config_path
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Reached the root directory
            break
        current_dir = parent_dir
    raise ConfigurationError(f"{root}/.caulconf")


def read_profile_yaml(home=os.path.expanduser("~")):
    if os.path.exists(f"{home}/.caulprofile"):
        with open(f"{home}/.caulprofile", "r") as f:
            profile = yaml.safe_load(f)
        return profile
    else:
        raise ConfigurationError(f"{home}/.caulprofile")