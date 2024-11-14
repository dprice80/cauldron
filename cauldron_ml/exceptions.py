class ProjectNotFoundError(Exception):
    def __init__(self, project_name):
        self.project_name = project_name
        super().__init__(f"The project {project_name} does not exist.")

class InvalidPipelineError(Exception):
    def __init__(self, pipeline_name):
        self.pipeline_name = pipeline_name
        super().__init__(f"The pipeline {pipeline_name} is invalid.")

class ConfigurationError(Exception):
    def __init__(self, config_name):
        self.config_name = config_name
        super().__init__(f"The configuration {config_name} is incorrect.")

class ExecutionError(Exception):
    def __init__(self, message):
        super().__init__(message)