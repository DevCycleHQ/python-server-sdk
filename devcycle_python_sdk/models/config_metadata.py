from devcycle_python_sdk.models.environment_metadata import EnvironmentMetadata
from devcycle_python_sdk.models.project_metadata import ProjectMetadata
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ConfigMetadata:
    project: ProjectMetadata
    environment: EnvironmentMetadata

    def to_json(self):
        result = {}
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            if value is not None:
                if field_name == "project" and isinstance(value, ProjectMetadata):
                    result[field_name] = value.to_json()
                elif field_name == "environment" and isinstance(
                    value, EnvironmentMetadata
                ):
                    result[field_name] = value.to_json()
                else:
                    result[field_name] = value
        return result

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
