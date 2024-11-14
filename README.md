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
docker-repo:
docker-base-image: europe-west2-docker.pkg.dev/msm-groupdata-sharedresources/base-images/python:3.12-slim
user-prefix: dprice
production-project-name: msmg-datascience-prod
sandbox-project-name: msmg-datascience-explore
production-service-account: robot-scientist@msmg-datascience-prod.iam.gserviceaccount.com
sandbox-service-account: robot-scientist@msmg-datascience-explore.iam.gserviceaccount.com
```
