# CauldronML: A CLI tool for building and deploying Kubeflow Pipelines in GCP Vertex AI

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

Note that ```docker-repo``` should include the namespace where the images are stored. The ```production-project-name``` and ```production-service-account``` can be the same as the sandbox accounts. In that case prod pipelines would run alongside dev pipelines in the same GCP project. However, this setup is not recommended. It is much safer to run a separate prod project, and for the deployment to prod to be executed by an automated workflow such as github actions. We will add examples to this effect shortly.

Now you are ready to build your first project. Cauldron has a built-in templating system, with one working example. More examples will be added at a later date.

```bash
caul create
```

This will give you a working example template. You should try building, deploying and running this template without modification to ensure installation succeeded and all permissions are set correctly on your account. The template will run with your user-prefix (from ~/.caulprofile).

CauldronML uses a two stage docker build to save time when making changes to your pipeline. First, build the base image.

```bash
caul build --base
```

Then build the pipeline image. 

```bash
caul build
```

NOTE: Running ```caul build``` with no base image present in the local or remote docker repo will trigger the automatic build of the base image.

Upload the images to your docker repo.

```bash
caul deploy
```

Run the pipeline.

```bash
caul run
```

You should now have a running pipeline.


## CI/CD Setting up GitHub Actions Workflows

Our intention is for users to build their own github actions that trigger when code is pushed to main via a PR. CauldronML works with kaniko to build both the base image and pipeline image. We will add detailed instructions on how to do this shortly.