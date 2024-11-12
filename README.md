# CauldronML: Vertex Pipelines Management

CauldronML is a comprehensive tool designed to simplify and manage the creation, activation, and deployment of Vertex pipelines. This package offers an array of functionalities tailored to streamline your machine learning operations, particularly within the Google Cloud Platform ecosystem.

## Features

- **Project Creation and Initialization**: Easily create new projects using predefined templates, ensuring consistent project structures.

- **Interactive Prompts**: Intuitive prompts guide users through setting up project details, GCP project IDs, service accounts, and more.

- **Configuration Management**: Store frequently used settings in a configuration file for quicker setup in future projects.

- **Pipeline Management**: Activate, list, clean, and build pipelines with ease, ensuring efficient project lifecycle management.

- **Docker Integration**: Check and manage Docker status, permissions, and build images necessary for deploying Vertex pipelines.

## Installation

You can install CauldronML using pip:

```bash
pip install cauldronml
```

## Usage

CauldronML is designed to be used via the command line interface (CLI) with typer. Below is an overview of the primary commands and their usage.

## Creating a New Project

To create a new project, use the create command. This command will guide you through selecting a template, setting up project details, and initializing the project structure.

## Cauldron Create

```bash
caul create 
```

### Optional Arguments

--project-name: The name of your project.
--template: The template to use for the project.
--project-root: The root directory for the project.
--user-prefix: A prefix for identifying the user.
--image-repo: The Docker image repository for storing and retrieving images.

Example with arguments

```bash
caul create --project-name my-project
```

## Activating a Project

To activate an existing project, use the activate command. This sets up the necessary environment for working on the specified project.

```bash
cauldron activate --name <project_name> --user-prefix <user_prefix>
```

Arguments
--name: The name of the project to activate.
--user-prefix: A prefix for identifying the user.

## Listing Pipelines

To list all available pipelines in your project directory, use the list command.

```bash
cauldron list
```

To clean up project files or Docker resources, use the clean command with the appropriate type (docker or files).

```bash
cauldron clean --type <type>
```

### Arguments

--type: The type of cleanup to perform (docker or files).

## Building a Pipeline

To build the Kubeflow pipeline from your project's components, use the build command.

```bash
cauldron build --version-tag <version_tag>
```

### Arguments

--version-tag: The version tag for the Docker image (default is latest).

## Deploying a Pipeline

To deploy the built pipeline to Vertex AI, use the deploy command.

```bash
cauldron deploy --version-tag <version_tag>
```

### Arguments

--version-tag: The version tag for the Docker image (default is latest).

## Configuration

CauldronML supports storing configurations in a .cauldron_config file in your home directory. This allows you to skip repetitive prompts for commonly used settings.

Example Configuration File

```ini
[DEFAULT]
MLOPS_PIPELINES_ROOT_PATH=/path/to/pipelines/root
MLOPS_USER_PREFIX=user_prefix
MLOPS_IMAGE_REPO=region-docker.pkg.dev/project/folder/
```

## Storing Configurations

When prompted during project creation or activation, you have the option to save your settings to a configuration file. This can be done interactively when you run the commands.

## Additional Utilities

CauldronML includes additional utility functions and classes to handle various tasks such as:

OS and Docker Checks: Functions to check the operating system type, Docker status, and permissions.
Environment Variable Management: Functions to load and manage environment variables for your project.
Component Image Building: Functions to build and tag Docker images for pipeline components.

## Exception Handling

CauldronML includes custom exceptions to handle common issues such as:

## Contribution

We welcome contributions to improve CauldronML. If you have suggestions, find bugs, or want to contribute new features, please open an issue or submit a pull request on GitHub.

## License

CauldronML is licensed under the MIT License. See the LICENSE file for more details.