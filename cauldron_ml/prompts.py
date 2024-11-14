import typer
from importlib.resources import files
import glob
import os


class TerminalColours:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def prompt_template(template_name: str = None):
    """
    This function allows the user to choose a template if more than one is found in the folder "pipelines/templates", 
    or automatically chooses the template if there is only one available. 
    If no templates are found, the function raises an exception.

    Args:
    cli_input_template (str): Existing input template. None to let function choose a template.

    Raises:
    Exception: Raises an exception of type TemplateNotFound if no templates are found matching pattern: pipelines/template*

    Returns:
    str: Chosen template's path.
    """
    while template_name is None:
        package_path = str(files("cauldron_ml"))
        template_folders = glob.glob(package_path + "/templates/*")
        if len(template_folders) > 1:
            typer.echo("Templates:")
            for ind, template in enumerate(template_folders):
                typer.echo(f"{str(ind + 1)}: {template}")
            template_ind = typer.prompt("Choose a template", type=int)
            if template_ind < 1 or template_ind > len(template_folders):
                typer.echo("Invalid template choice. Please try again.")
                continue
            template_name = template_folders[template_ind - 1]
        elif len(template_folders) == 1:
            typer.echo(
                f"{TerminalColours.HEADER}Using template:{TerminalColours.ENDC}")
            template_name = template_folders[0]
            typer.echo(template_name)
        else:
            raise TemplateNotFound(
                f"Cannot find any templates matching pattern: {package_path}/templates/*"
            )
    return template_name


def prompt_project_name(project_root: str, project_name: str):
    """
    Validates the project name and path, prompting the user interactively in case of issues.

    This function continuously prompts the user for a valid project name until a valid name is provided. If the project root
    already exists, the user is asked whether to continue with the existing project.

    Args:
        qualified_project_root (str): The absolute path to the project root directory.
        cli_input_project_name (str): The project name inputted via the command-line interface.

    Returns:
        str: The validated project name.

    Raises:
        ValueError: If the project name contains underscores.

    Note:
        Project names cannot contain underscores; dashes are allowed.
    """
    valid_path = False
    while not valid_path:
        if os.path.isdir(
            f"{project_root}/pipelines/{project_name}"
        ):
            init_existing_project = typer.prompt(
                f"""
                {TerminalColours.WARNING}The project path {project_root} already exists.
                Do you want to continue with this existing project and re-initialise (y/n)?{TerminalColours.ENDC}
                """
            )
            if init_existing_project == "y":
                valid_path = True
            elif init_existing_project == "n":
                valid_path = False
                project_name = ""
        elif project_name is None:
            valid_path = False
        elif "_" in project_name:
            typer.echo("Name must not contain underscores (dashes are allowed)")
        else:
            valid_path = True
        if not valid_path:
            project_name = typer.prompt(
                f"{TerminalColours.HEADER}Project name{TerminalColours.ENDC}", type=str
            )
            print(
                f"{project_root}/pipelines/{project_name}/"
            )
    return project_name
