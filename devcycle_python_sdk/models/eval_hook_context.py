from typing import Any, Optional

from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.config_metadata import ConfigMetadata


class HookContext:
    def __init__(self, key: str, user: DevCycleUser, default_value: Any, metadata: Optional[ConfigMetadata] = None):
        self.key = key
        self.default_value = default_value
        self.user = user
        self.metadata = metadata

    def get_metadata(self) -> Optional[ConfigMetadata]:
        """Get the configuration metadata associated with this evaluation context"""
        return self.metadata
