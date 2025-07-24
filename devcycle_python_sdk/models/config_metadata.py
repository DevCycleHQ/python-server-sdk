from dataclasses import dataclass
from typing import Optional


@dataclass
class ProjectMetadata:
    """Project information metadata"""
    id: str
    key: str

    @classmethod
    def from_json(cls, data: dict) -> "ProjectMetadata":
        return cls(
            id=data.get("_id", ""),
            key=data.get("key", ""),
        )


@dataclass
class EnvironmentMetadata:
    """Environment information metadata"""
    id: str
    key: str

    @classmethod
    def from_json(cls, data: dict) -> "EnvironmentMetadata":
        return cls(
            id=data.get("_id", ""),
            key=data.get("key", ""),
        )


@dataclass
class ConfigMetadata:
    """Configuration metadata containing project, environment, and versioning information"""
    config_etag: Optional[str]
    config_last_modified: Optional[str]
    project: Optional[ProjectMetadata]
    environment: Optional[EnvironmentMetadata]

    @classmethod
    def from_config_response(
        cls,
        config_data: dict,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
    ) -> "ConfigMetadata":
        """Create ConfigMetadata from API response data and headers"""
        project_data = config_data.get("project", {})
        environment_data = config_data.get("environment", {})
        
        return cls(
            config_etag=etag,
            config_last_modified=last_modified,
            project=ProjectMetadata.from_json(project_data) if project_data else None,
            environment=EnvironmentMetadata.from_json(environment_data) if environment_data else None,
        )

    def __str__(self) -> str:
        return f"ConfigMetadata(etag={self.config_etag}, last_modified={self.config_last_modified}, project={self.project}, environment={self.environment})"