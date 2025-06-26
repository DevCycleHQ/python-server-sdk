from typing import Any

from devcycle_python_sdk.models.user import DevCycleUser


class HookContext:
    def __init__(self, key: str, user: DevCycleUser, default_value: Any):
        self.key = key
        self.default_value = default_value
        self.user = user
