from devcycle_python_sdk.models.environment_metadata import EnvironmentMetadata
from devcycle_python_sdk.models.project_metadata import ProjectMetadata
from typing import Dict, Any, Optional
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
    def from_json(json_obj: Optional[Dict[str, Any]]) -> Optional["ConfigMetadata"]:
        if json_obj is None:
            return None
        project = ProjectMetadata.from_json(json_obj.get("project"))
        environment = EnvironmentMetadata.from_json(json_obj.get("environment"))

        if project is None or environment is None:
            return None

        return ConfigMetadata(
            project=project,
            environment=environment,
        )
