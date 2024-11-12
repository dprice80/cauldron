import yaml
import pytest
from cauldron_ml.cli import (
    CauldronMLConfig,
    prompt_template,
    TerminalColours,
    TemplateNotFound
    )
import subprocess
import os


def test_write_config_yaml():
    # Define a config dictionary to write to the file
    config_contents = {
        'CAUL_PIPELINES_IMAGE_REPO': 'europe-west2-docker.pkg.dev/msm-groupdata-sharedresources/data-science-ml-pipelines',
        'CAUL_PIPELINES_IMAGE_TAG': 'europe-west2-docker.pkg.dev/msm-groupdata-sharedresources/data-science-ml-pipelines/unit_test_component:latest',
        'CAUL_PIPELINES_PROJECT_PATH': '/home/darren_price_moneysupermarket_co/dsmlp-dependabot/cauldron-ml/tests/pipelines/unit_test',
        'CAUL_PIPELINES_ROOT_PATH': '/home/darren_price_moneysupermarket_co/dsmlp-dependabot/cauldron-ml/tests',
        'CAUL_PROJECT_NAME': 'unit_test',
        'CAUL_USER_PREFIX': 'unit_test'
        }

    # Call the function to write the config to the file
    config = CauldronMLConfig(
        project_root=os.getcwd(),
        project_name="unit_test",
        user_prefix="unit_test",
        image_repo="europe-west2-docker.pkg.dev/msm-groupdata-sharedresources/data-science-ml-pipelines",
        config_dir=os.getcwd()
        )

    config.write_config_yaml()

    # Open the file again and load the contents
    with open(config.config_file, 'r') as f:
        loaded_config = yaml.safe_load(f)

    # Check that the loaded config matches the original config
    assert loaded_config == config_contents


def test_prompt_template_multiple_templates(mocker):
    # Arrange
    mocker.patch('glob.glob', return_value=['template1', 'template2'])
    mocker.patch('typer.prompt', return_value=2)
    mock_echo = mocker.patch('typer.echo')

    # Act
    result = prompt_template(None)

    # Assert
    assert result == 'template2'
    mock_echo.assert_any_call('Templates:')
    mock_echo.assert_any_call('1: template1')
    mock_echo.assert_any_call('2: template2')


def test_prompt_template_single_template(mocker):
    # Arrange
    mock_glob = mocker.patch('glob.glob', return_value=['template1'])
    mock_echo = mocker.patch('typer.echo')

    # Act
    result = prompt_template(None)

    # Assert that the returned value is correct
    assert result == 'template1'
    # Assert that the echo/glob functions were called with the correct arguments in prompt_template
    mock_echo.assert_any_call(f"{TerminalColours.HEADER}Using template:{TerminalColours.ENDC}")
    mock_echo.assert_any_call('template1')
    mock_glob.assert_any_call("pipelines/templates/*")


def test_prompt_template_with_input(mocker):
    # Arrange
    mocker.patch('glob.glob', return_value=['template1', 'template2'])
    mock_echo = mocker.patch('typer.echo')

    # Act
    result = prompt_template('template1')

    # Assert
    assert result == 'template1'
    mock_echo.assert_not_called()


def test_prompt_template_with_invalid_input(mocker):
    # Arrange
    mocker.patch('glob.glob', return_value=['template1', 'template2'])
    mocker.patch('typer.prompt', return_value=3)
    mock_echo = mocker.patch('typer.echo')

    # Act
    result = prompt_template(None)

    # Assert
    assert result == 'template1'
    mock_echo.assert_any_call('Invalid choice. Please select a valid template number.')


def test_prompt_template_with_invalid_input_then_valid_input(mocker):
    # Arrange
    mocker.patch('glob.glob', return_value=['template1', 'template2'])
    mocker.patch('typer.prompt', return_value=[3, 2])
    mock_echo = mocker.patch('typer.echo')

    # Act
    error_raised = False
    try:
        prompt_template(None)
    except TemplateNotFound:
        error_raised = True

    # Assert
    assert error_raised
    mock_echo.assert_any_call("Invalid template choice. Please try again.")


def test_caul_build():
    subprocess.run([dedent("""
                    caul create --name=test_penguin --template=penguin_example --image-repo
                    
                    """)])
