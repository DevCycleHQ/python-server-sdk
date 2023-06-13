# ruff: noqa: N815
from dataclasses import dataclass, field
from time import time
from typing import Dict, Optional


@dataclass(order=False)
class User:
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    appVersion: Optional[str] = None
    appBuild: Optional[str] = None
    customData: Dict[str, str] = field(default_factory=dict)
    privateCustomData: Dict[str, str] = field(default_factory=dict)
    createdDate: int = field(default_factory=lambda: int(time()))
    lastSeenDate: Optional[int] = None  # TODO: accept datetime
    platform: Optional[str] = None
    platformVersion: Optional[str] = None
    deviceModel: Optional[str] = None
    sdkType: Optional[str] = None
    sdkVersion: Optional[str] = None

    def to_json(self):
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None
        }
