from devcycle_python_sdk.models.environment_metadata import EnvironmentMetadata
from devcycle_python_sdk.models.project_metadata import ProjectMetadata
import json


class ConfigMetadata:
    def __init__(
        self,
        project: ProjectMetadata,
        environment: EnvironmentMetadata,
    ):
        self.project = project
        self.environment = environment

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__)

    @staticmethod
    def from_json(json_str: str) -> "ConfigMetadata":
        if json_str is None:
            return None
        return ConfigMetadata(
            project=ProjectMetadata.from_json(json_str["project"]),
            environment=EnvironmentMetadata.from_json(json_str["environment"]),
        )