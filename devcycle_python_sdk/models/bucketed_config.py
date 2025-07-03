from dataclasses import dataclass
from typing import Dict, List
from typing import Optional

from .user import DevCycleUser
from .variable import Variable
from .feature import Feature


@dataclass
class EdgeDBSettings:
    enabled: bool

    @classmethod
    def from_json(cls, data: dict) -> "EdgeDBSettings":
        return cls(
            enabled=data.get("enabled", False),
        )


@dataclass
class OptInColors:
    primary: str
    secondary: str

    @classmethod
    def from_json(cls, data: dict) -> "OptInColors":
        return cls(
            primary=data.get("primary", ""),
            secondary=data.get("secondary", ""),
        )


@dataclass
class OptInSettings:
    enabled: bool
    title: str
    description: str
    image_url: str
    colors: OptInColors

    @classmethod
    def from_json(cls, data: dict) -> "OptInSettings":
        return cls(
            enabled=data.get("enabled", False),
            title=data.get("title", ""),
            description=data.get("description", ""),
            image_url=data.get("imageURL", ""),
            colors=OptInColors.from_json(data.get("colors", "")),
        )


@dataclass
class ProjectSettings:
    edge_db: Optional[EdgeDBSettings]
    opt_in: Optional[OptInSettings]
    disable_passthrough_rollouts: Optional[bool]

    @classmethod
    def from_json(cls, data: dict) -> "ProjectSettings":
        return cls(
            edge_db=(
                EdgeDBSettings.from_json(data["edgeDB"]) if "edgeDB" in data else None
            ),
            opt_in=OptInSettings.from_json(data["optIn"]) if "optIn" in data else None,
            disable_passthrough_rollouts=data.get("disablePassthroughRollouts", False),
        )


@dataclass
class Project:
    id: str
    key: str
    a0_organization: str
    settings: Optional[ProjectSettings]

    @classmethod
    def from_json(cls, data: dict) -> "Project":
        return cls(
            id=data["_id"],
            key=data["key"],
            a0_organization=data["a0_organization"],
            settings=(
                ProjectSettings.from_json(data["settings"])
                if "settings" in data
                else None
            ),
        )


@dataclass
class Environment:
    id: str
    key: str

    @classmethod
    def from_json(cls, data: dict) -> "Environment":
        return cls(
            id=data["_id"],
            key=data["key"],
        )


@dataclass
class FeatureVariation:
    feature: str
    variation: str

    @classmethod
    def from_json(cls, data: dict) -> "FeatureVariation":
        return cls(
            feature=data["_feature"],
            variation=data["_variation"],
        )


@dataclass(order=False)
class BucketedConfig:
    project: Project
    environment: Environment
    features: Dict[str, Feature]
    feature_variation_map: Dict[str, str]
    variable_variation_map: Dict[str, FeatureVariation]
    variables: Dict[str, Variable]
    known_variable_keys: List[float]

    user: Optional[DevCycleUser] = None

    def to_json(self):
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None
        }

    @classmethod
    def from_json(cls, data: dict) -> "BucketedConfig":
        return cls(
            project=Project.from_json(data["project"]),
            environment=Environment.from_json(data["environment"]),
            features={
                k: Feature.from_json(v) for k, v in data.get("features", {}).items()
            },
            feature_variation_map=data.get("featureVariationMap", {}),
            variable_variation_map={
                k: FeatureVariation.from_json(v)
                for k, v in data.get("variableVariationMap", {}).items()
            },
            variables={
                k: Variable.from_json(v) for k, v in data.get("variables", {}).items()
            },
            known_variable_keys=data.get("knownVariableKeys", []),
        )
