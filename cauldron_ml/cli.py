import os
import shutil
import typer
import glob
import subprocess as sub
from textwrap import dedent
from enum import Enum
from pathlib import Path
from cauldron_ml.exceptions import ExecutionError
from cauldron_ml import __path__ as cauldron_package_path
import re
from .prompts import (
    prompt_project_name,
    prompt_template
)
from .config import (
    write_config_yaml,
    read_config_yaml,
    read_profile_yaml
)

app = typer.Typer()


class TemplateNotFound(Exception):
    pass


# This callback is used to display the help message
@app.callback()
def callback():
    """
    CauldronML: Manage your Vertex AI pipelines with ease.

    Welcome to CauldronML, a powerful tool for managing Vertex AI pipelines.
    This package allows you to create, activate, list, and clean up pipelines
    through an easy-to-use command line interface.

    For detailed help on each command, use:
    caul <command> --help
    """


@app.command()
def init():
    home_dir = os.path.expanduser("~")
    profile_path = os.path.join(home_dir, ".caulprofile")

    if not os.path.exists(profile_path):
        with open(profile_path, "w") as profile_file:
            profile_file.write(dedent("""
                docker-repo: your-docker-repo
                docker-base-image: your-docker-base-image
                user-prefix: your-user-prefix
                production-project-name: your-production-project-name
                sandbox-project-name: your-sandbox-project-name
                production-service-account: your-production-service-account
                sandbox-service-account: your-sandbox-service-account
            """))
        typer.echo(f"Created .caulprofile at {profile_path}")
    else:
        typer.echo(f".caulprofile already exists at {profile_path}")

    # Set up folder structure
    project_root = os.getcwd()
    pipelines_path = os.path.join(project_root, "pipelines")
    if not os.path.exists(pipelines_path):
        os.makedirs(pipelines_path)
        typer.echo(f"Created pipelines directory at {pipelines_path}")
    else:
        typer.echo(f"Pipelines directory already exists at {pipelines_path}")


@app.command()
def create(
    name: str = None,
    template: str = None
):
    """
    Create a new project.

    This function initializes a new project in the 'pipelines' directory of the repository.
    It ensures that the current working directory is the root of the repository and then
    proceeds to create a new project directory based on the provided template.

    Args:
        name (str, optional): The name of the new project. If not provided, the user will be prompted to enter one.
        template (str, optional): The name of the template to use for the new project. If not provided, the user will be prompted to select one.

    Raises:
        FileNotFoundError: If the current working directory is not the root of the repository.
        ExecutionError: If there is an error during the execution of the command to copy and rename the template files.

    Returns:
        None
    """

    if not os.path.isdir("pipelines"):
        raise FileNotFoundError("You must be in the root of the repository to create a project")

    profile = read_profile_yaml()
    docker_image_respository = profile['docker-repo']

    project_root = os.getcwd()

    qualified_template = prompt_template(template_name=template)

    qualified_project_name = prompt_project_name(
        project_root=project_root,
        project_name=name,
    )

    project_root = Path(project_root)
    docker_image_respository = Path(docker_image_respository)
    project_path = str(project_root / f"pipelines/{qualified_project_name}")

    project_path = f"{str(project_root)}/pipelines/{qualified_project_name}"
    if not os.path.isdir(project_path):
        cmd = f"""
            cp -R {qualified_template} {str(project_root)}/pipelines/{qualified_project_name}
            mv {str(project_root)}/pipelines/{qualified_project_name}/dags/*.py \\
                {str(project_root)}/pipelines/{qualified_project_name}/dags/{qualified_project_name}_dag.py
        """
        response = sub.run(
            cmd,
            stdout=sub.PIPE,
            stderr=sub.PIPE,
            shell=True,
            check=True
        )
        if response.stderr != b"":
            raise ExecutionError(f"Failed to execute command {cmd}: {str(response.stderr)}")
    else:
        typer.echo(f"Project folder already exists: {project_path}")

    activate(qualified_project_name)


@app.command()
def activate(name: str, user_prefix: str = None, version_tag: str = "latest"):
    """
    Activate an existing project
    """

    if not os.path.isdir("pipelines"):
        raise FileNotFoundError("You must be in the root of the repository to activate a project")

    project_root = os.getcwd()

    if not os.path.isdir(
        f"{project_root}/pipelines/{name}"
    ):
        raise Exception(f"The project {name} does not exist.")

    profile = read_profile_yaml()
    user_prefix = profile['user-prefix']
    docker_image_repo = Path(profile['docker-repo'])
    project_root = Path(project_root)
    docker_base_image = profile['docker-base-image']

    write_config_yaml(
        caul_pipelines_project_path=str(project_root / f"pipelines/{name}"),
        caul_pipelines_root_path=str(project_root),
        caul_pipelines_image_tag=str(docker_image_repo / f"{name}_component:{user_prefix}_{version_tag}"),
        caul_pipelines_image_repo=str(docker_image_repo),
        caul_project_name=name,
        caul_docker_base_image=docker_base_image
        )

    typer.echo(f"[CauldronML] Activated project {name}.")


@app.command(name="list")
def list_pipelines():
    """
    List pipelines from pipelines/
    """
    pipelines = glob.glob("pipelines//*")
    for p in pipelines:
        typer.echo(p.replace("pipelines//", ""))


class CleanType(str, Enum):
    docker = "docker"
    files = "files"


@app.command()
def clean(type: CleanType):
    """
    Clean up project files
    """
    if type == "docker":
        sub.run(
            """
            docker container prune
            docker image prune
        """,
            shell=True,
            check=True
        )

    if type == "files":
        typer.echo("Not implemented yet - clean up your own files! ;)")


def build_kfp_components_image(build_image: bool = False):
    """
    Build kubeflow components in ./vdist
    """

    config = read_config_yaml()
    os.chdir(f"{config['CAUL_PIPELINES_ROOT_PATH']}/vdist")

    if not os.path.isdir(f"{config['CAUL_PIPELINES_ROOT_PATH']}/logs"):
        os.mkdir(f"{config['CAUL_PIPELINES_ROOT_PATH']}/logs")

    if build_image:
        build_image_flag = ""
    else:
        build_image_flag = " --no-build-image"

    command = f"""
        export PYTHONPATH="$PYTHONPATH:$PWD"
        kfp components build . --component-filepattern component*.py --no-push-image{build_image_flag}
        if [ -f Dockerfile ]; then
            rm Dockerfile
        fi
    """

    with open(f"{config['CAUL_PIPELINES_ROOT_PATH']}/logs/kfp-build.log", "w") as log_file:
        process = sub.Popen(command, shell=True, stdout=sub.PIPE, stderr=sub.STDOUT, text=True)
        for line in process.stdout:
            print(line, end='')  # Print to terminal
            log_file.write(line)  # Write to log file
        process.wait()


def rename_docker_image(old_image_name: str, new_tag: str):
    # Split the old image name into name and tag
    old_name, old_tag = old_image_name.split(':')
    # Create the new image name
    new_image_name = f"{old_name}:{new_tag}"
    return new_image_name


def check_base_image_exists():
    config = read_config_yaml()
    profile = read_profile_yaml()
    image_path, _ = config["CAUL_PIPELINES_IMAGE_TAG"].split(':')
    typer.echo("[CauldronML] Checking for ")
    result = sub.run(f"gcloud container images list-tags --filter base {image_path}", shell=True, check=True, stdout=sub.PIPE)
    if "base" in result.stdout.decode():
        return True

    # Check if the image exists locally
    tag = f"{profile['user-prefix']}_base"
    local_result = sub.run(f"docker images -q {image_path}:{tag}", shell=True, check=True, stdout=sub.PIPE)
    image_id = local_result.stdout.decode().strip()

    # Validate the image ID format (12 hexadecimal characters)
    if re.match(r'^[a-f0-9]{12}$', image_id):
        return True

    return False


def fun_build_base_image(use_cache: bool = True):

    profile = read_profile_yaml()
    config = read_config_yaml()

    base_image = rename_docker_image(config["CAUL_PIPELINES_IMAGE_TAG"], f"{profile['user-prefix']}_base")

    if use_cache:
        cache_flag = ""
    else:
        cache_flag = " --no-cache"

    typer.echo(f"\n[CauldronML] Building base image: {base_image}\n")

    base_dockerfile = str(Path(cauldron_package_path[0]) / "docker/BaseDockerfile")

    sub.run(f"""
            set -e
            cd {config["CAUL_PIPELINES_ROOT_PATH"]}
            docker build{cache_flag} -t {base_image} -f {base_dockerfile} --build-arg PROJECT_NAME={config['CAUL_PROJECT_NAME']} --build-arg BASE_IMAGE={config['CAUL_PIPELINES_DOCKER_BASE_IMAGE']} . | tee docker_base_build.log
            """, shell=True, check=True)

    typer.echo(f"\n[CauldronML] Base image built: {base_image}\n")


@app.command()
def build(use_cache: bool = False,
          use_docker: bool = True,
          base: bool = False,
          push: bool = False
          ):
    """
    Build the kubeflow pipeline from the active project's components

    Args:
        version_tag (str, optional): The version tag for the pipeline image. Defaults to "latest".
        build_image (bool, optional): Whether to build the pipeline image. Defaults to True.
        docker_build (bool, optional): Whether to use Docker for building the pipeline. Defaults to True.
        base (bool, optional): Whether to build the base image. Defaults to False.
        push_image (bool, optional): Whther to push the base / pipeline image after building

    Raises:
        ValueError: If `version_tag` is set when building the base image.
        ValueError: If `local-build` is True while `build-image` is False.

    Returns:
        None
    """

    config = read_config_yaml()
    profile = read_profile_yaml()

    # Copy the base image dockerfile into the project repo and build it
    if base:
        fun_build_base_image(use_cache=use_cache)
        if push:
            deploy(images=["base"])
        return None

    if use_docker:
        if not check_base_image_exists():
            fun_build_base_image(use_cache=use_cache)
            if push:
                deploy(images=["base"])
        IMAGE_NAME = config["CAUL_PIPELINES_IMAGE_TAG"]
        _, IMAGE_TAG = config["CAUL_PIPELINES_IMAGE_TAG"].split(":")
        _, VERSION_TAG = IMAGE_TAG.split("_")
        user_prefix = profile['user-prefix']
        project_name = config['CAUL_PROJECT_NAME']
        if use_cache is False:
            use_cache_arg = " --no-cache"
        else:
            use_cache_arg = ""

        dockerfile = str(Path(cauldron_package_path[0]) / "docker/Dockerfile")
        run_command = dedent(f"""\
            cd {config['CAUL_PIPELINES_ROOT_PATH']}
            docker build -t {IMAGE_NAME} -f {dockerfile}{use_cache_arg} \
            --build-arg PROJECT_NAME={project_name} \
            --build-arg IMAGE_TAG={VERSION_TAG} \
            --build-arg USER_PREFIX={user_prefix} \
            --build-arg DOCKER_REPO="{config['CAUL_PIPELINES_IMAGE_REPO']}" \
            --build-arg PRODUCTION_SERVICE_ACCOUNT="{profile['production-service-account']}" \
            --build-arg SANDBOX_SERVICE_ACCOUNT="{profile['sandbox-service-account']}" \
            --build-arg DOKER_BASE_IMAGE="{profile['docker-base-image']}" .\
            """)
        sub.run(run_command, shell=True, check=True)

    typer.echo("\n[CauldronML] Building kubeflow pipeline\n")
    src_location = config["CAUL_PIPELINES_ROOT_PATH"] + "/vdist"
    if os.path.isdir(src_location):
        shutil.rmtree(src_location)

    typer.echo("\n[CauldronML] Copying files and building image\n")
    sub.run(
        f"""
        mkdir {config['CAUL_PIPELINES_ROOT_PATH']}/vdist
        cp -rf {config['CAUL_PIPELINES_PROJECT_PATH']}/model/* {config['CAUL_PIPELINES_ROOT_PATH']}/vdist
        cp -rf {config['CAUL_PIPELINES_PROJECT_PATH']}/build/* {config['CAUL_PIPELINES_ROOT_PATH']}/vdist
        cp -rf {config['CAUL_PIPELINES_ROOT_PATH']}/cauldron-ml {config['CAUL_PIPELINES_ROOT_PATH']}/vdist
    """,
        shell=True,
        check=True
    )

    typer.echo(
        "\n[CauldronML] Files copied to /vdist. DO NOT EDIT FILES IN vdist n")

    build_kfp_components_image(build_image=False)


@app.command()
def deploy(images=["base", "pipeline"]):
    """
    Deploy Docker images to the repository.
    
    This command pushes the specified Docker images to the repository. By default,
    it pushes the "base" and "pipeline" images with the "latest" version tag.
    Args:
        version_tag (str): The version tag to use for the images. Defaults to "latest".
        images (list): A list of image types to push. Defaults to "base, pipeline".
    Raises:
        subprocess.CalledProcessError: If the docker push command fails.
    Usage:
        caul deploy --images "base, pipeline"
    Notes:
        - The configuration is read from a YAML file.
        - The image tags are renamed based on the provided version tag.
        - Only the specified images in the `images` list are pushed.
    """

    config = read_config_yaml()
    profile = read_profile_yaml()
    image_tag = config["CAUL_PIPELINES_IMAGE_TAG"]
    base_image_tag = rename_docker_image(config["CAUL_PIPELINES_IMAGE_TAG"], f"{profile['user-prefix']}_base")
    if "base" in images:
        typer.echo(f"\n[CauldronML] Pushing image: {base_image_tag}\n")
        sub.run(f"docker push {base_image_tag}", shell=True, check=True)
    if "pipeline" in images:
        typer.echo(f"\n[CauldronML] Pushing image: {image_tag}\n")
        sub.run(f"docker push {image_tag}", shell=True, check=True)


@app.command()
def build_deploy_run():
    """
    Run build, deploy and run steps
    """
    config = read_config_yaml()
    build()
    deploy()
    os.chdir(config["CAUL_PIPELINES_ROOT_PATH"])
    run()


@app.command()
def build_deploy():
    """
    Run build and deploy steps
    """
    build()
    deploy()


@app.command()
def run():
    """
    Run the pipeline
    """
    config = read_config_yaml()
    sub.run(
        f"""
        cd {config['CAUL_PIPELINES_ROOT_PATH']}/vdist
        python run.py
    """,
        shell=True,
        check=True
    )


@app.command()
def info():
    """
    Get info on the current activated project
    """
    config = read_config_yaml()
    profile = read_profile_yaml()
    configpath = read_config_yaml(return_path=True)
    profilepath = os.path.expanduser("~") + "/.caulprofile"
    typer.echo(
        dedent(
            f"""
                Config Path: {configpath}
                Profile Path: {profilepath}

                Config:
                CAUL_PIPELINES_ROOT_PATH       {config['CAUL_PIPELINES_ROOT_PATH']}
                CAUL_PIPELINES_PROJECT_PATH    {config['CAUL_PIPELINES_PROJECT_PATH']}
                CAUL_PROJECT_NAME              {config['CAUL_PROJECT_NAME']}
                CAUL_PIPELINES_IMAGE_TAG       {config['CAUL_PIPELINES_IMAGE_TAG']}

                Profile:
                docker-repo                    {profile['docker-repo']}
                user-prefix                    {profile['user-prefix']}
                production-project-name        {profile['production-project-name']}
                sandbox-project-name           {profile['sandbox-project-name']}
            """
        )
    )


@app.command()
def test():
    """
    Run tests located in the currently active project folder
    """
    config = read_config_yaml()
    project_path = config['CAUL_PIPELINES_PROJECT_PATH']
    test_path = f"{project_path}/tests"

    typer.echo("\n[CauldronML] Running tests\n")
    typer.echo(f"pytest {test_path}")

    # Check if the test directory exists
    if not os.path.isdir(test_path):
        typer.echo(f"\n[CauldronML] Test directory {test_path} does not exist.\n")
        return

    # List files in the test directory
    typer.echo("\n[CauldronML] Files in the test directory:\n")
    for root, dirs, files in os.walk(test_path):
        for file in files:
            typer.echo(os.path.join(root, file))

    # Run pytest
    result = sub.run(
        f"""
        cd {project_path}
        python -m pytest {test_path}
        """,
        shell=True,
        capture_output=True,
        text=True,
        check=True
    )
 
    # Output the result
    typer.echo(result.stdout)
    typer.echo(result.stderr)
