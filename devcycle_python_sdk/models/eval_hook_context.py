from typing import Any, Optional
from dataclasses import dataclass

from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.config_metadata import ConfigMetadata


@dataclass
class HookContext:
    key: str
    user: DevCycleUser
    default_value: Any
    config_metadata: Optional[ConfigMetadata] = None

    def to_json(self):
        result = {}
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            if value is not None:
                if field_name == "config_metadata" and isinstance(value, ConfigMetadata):
                    result[field_name] = value.to_json()
                elif field_name == "user" and isinstance(value, DevCycleUser):
                    result[field_name] = value.to_json()
                else:
                    result[field_name] = value
        return result

    def __str__(self):
        return f"HookContext(key={self.key}, user={self.user}, default_value={self.default_value}, config_metadata={self.config_metadata})"

    def __repr__(self):
        return self.__str__()