# CauldronML: A lightweight CLI tool and python toolbox for creating, building and deploying production-ready Vertex Kubeflow Pipelines

## Quickstart (10 mins)

Before you start, we recommend installing a python environment manager. Cauldron uses uv in the build process for it's speed, but you don't need to use it locally. We prefer pyenv for it's user-friendliness and automatic switching between projects.

If you don't already have one installed, you can install pyenv in one line.

## Installation requirements

Cauldron works with unix-based systems like MacOS and Linux. It does not currently work on Windows. For windows users, we recommend installing Windows Subsystem for Linux (WSL) but we have not tested this.

### Install pyenv

```bash
curl https://pyenv.run | bash
```

### Install a compatible python version and virtual envioronment

Python >=3.10 is supported, although python >=3.12 is recommended as this will allow you to use the latest versions of kubeflow (kfp) and google-cloud-aiplatform.

Start with a blank folder

```bash
mkdir my-project
cd my-project
```

Install python 3.12, create a new virtualenv and set it to auto-activate in the current folder

```bash
pyenv install 3.12
pyenv virtualenv 3.12 my-project
pyenv local my-project
```

### Install cauldron-ml

```bash
pip install git+https://github.com/dprice80/cauldron-ml.git
```

### Verify the installation and check the CLI tool is registered

```bash
caul --help
```

Help output should be displayed

### Initialise Cauldron

```bash
caul init
```

This will create a yaml file called ~/.caulprofile. This file should be modified by the user with the following settings:

```yaml 
docker-repo: <repo-address>/subfolder  # no trailing slash
docker-base-image: python:3.12-slim  # By default, cauldron pipelines work with slim versions of python images (tested with 3.12).
user-prefix: jbloggs
production-project-name: foo-bar-prod
sandbox-project-name: foo-bar-sandbox
production-service-account: my-sa@foo-bar-prod@iam.gserviceaccount.com
sandbox-service-account: my-sa@foo-bar-sandbox@iam.gserviceaccount.com
```

Note that ```docker-repo``` should include the folder where the images are stored. The ```production-project-name``` and ```production-service-account``` can be the same as the sandbox accounts. The prefix and image tags are set within the CI pipeline workflow, not by cauldron, so the user can decide to run all production pipelines and development pipelines in the same GCP project, although we do not recommend this.

We will soon add a github action to take care of the build process, setting the arguments correctly etc. At MSM we use a matrix build strategy to build all our pipelines within a mono-repo, only building new images when we detect a change in that project.

```bash
caul create
```

```bash
caul build --base
```

```bash
caul build
```

```bash
caul deploy
```

```bash
caul run
```

You should now have a running pipeline.

