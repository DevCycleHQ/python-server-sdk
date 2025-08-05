from typing import Any

from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.config_metadata import ConfigMetadata

class HookContext:
    def __init__(self, key: str, user: DevCycleUser, default_value: Any, config_metadata: ConfigMetadata = None):
        self.key = key
        self.default_value = default_value
        self.user = user
        self.config_metadata = config_metadata
