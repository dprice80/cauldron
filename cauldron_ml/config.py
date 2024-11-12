import yaml
import os
from .exceptions import ConfigurationError


def write_config_yaml(
            caul_pipelines_root_path: str = None,
            caul_pipelines_image_repo: str = None, caul_pipelines_project_path: str = None,
            caul_project_name: str = None, caul_pipelines_image_tag: str = None, config: dict = None
        ):

    if config:
        pass
    else:
        config = {
            'CAUL_PIPELINES_ROOT_PATH': caul_pipelines_root_path,
            'CAUL_PIPELINES_IMAGE_REPO': caul_pipelines_image_repo,
            'CAUL_PIPELINES_PROJECT_PATH': caul_pipelines_project_path,
            'CAUL_PROJECT_NAME': caul_project_name,
            'CAUL_PIPELINES_IMAGE_TAG': caul_pipelines_image_tag
        }

    root = os.getcwd()
    with open(f"{root}/.caulconf", "w") as f:
        yaml.dump(config, f)


def read_config_yaml(root: str = os.getcwd()):
    current_dir = root
    while True:
        if current_dir == os.path.expanduser("~"):
            break  # Don't read from the user directory
        config_path = os.path.join(current_dir, '.caulconf')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
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
    elif os.path.exists(".caulprofile"):
        with open(".caulprofile", "r") as f:
            profile = yaml.safe_load(f)
    else:
        raise ConfigurationError(f"{home}/.caulprofile")