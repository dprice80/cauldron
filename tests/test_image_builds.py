import pytest
import subprocess
import os

DOCKER_REPO = "europe-west2-docker.pkg.dev/msm-groupdata-sharedresources/data-science-ml-pipelines"
PROJECT_NAME = "kaniko-test"
PREFIX = "dprice"
IMAGE_NAME = f"{DOCKER_REPO}/{PROJECT_NAME}_component"

@pytest.fixture(scope="module", autouse=True)
def setup_caul_profile():
    """Sets up the .caulprofile before tests and removes it afterwards."""
    with open(os.path.expanduser("~/.caulprofile"), "w") as f:
        f.write(f"docker-repo: {DOCKER_REPO}\n")
        f.write(f"user-prefix: {PREFIX}\n")
        f.write("production-project-name: msmg-datascience-prod\n")
        f.write("production-project-numeric-id: '612279675388'\n")
        f.write("sandbox-project-name: msmg-datascience-explore\n")
        f.write("sandbox-project-numeric-id: '243205181736'\n")
    yield
    os.remove(os.path.expanduser("~/.caulprofile"))


@pytest.fixture(scope="module")
def remove_images():
    """Removes docker images before tests, doesn't check for errors."""
    subprocess.run(["docker", "rmi", "-f", f"{IMAGE_NAME}:{PREFIX}_base"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    subprocess.run(["docker", "rmi", "-f", f"{IMAGE_NAME}:{PREFIX}_latest"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)


def run_command(command):
    """Runs a command and returns the result."""
    print(f"Running command: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = [], []

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
            stdout.append(output.strip())

    stderr_output = process.stderr.read()
    if stderr_output:
        print(stderr_output.strip())
        stderr.append(stderr_output.strip())

    return process.returncode, '\n'.join(stdout), '\n'.join(stderr)


def check_image_exists(image_name):
    """Checks if a docker image exists."""
    result = subprocess.run(["docker", "images"], capture_output=True, text=True, check=False)
    return image_name in result.stdout


def test_build_base_image(remove_images):
    run_command(f"caul activate {PROJECT_NAME}")
    run_command("caul build --base --no-push")
    assert check_image_exists(f"{IMAGE_NAME}:{PREFIX}_base"), f"Base image {IMAGE_NAME}:{PREFIX}_base not found."


def test_build_latest_image():
    run_command("caul build --no-push")
    assert check_image_exists(f"{IMAGE_NAME}:{PREFIX}_latest"), f"Latest image {IMAGE_NAME}:{PREFIX}_latest not found."