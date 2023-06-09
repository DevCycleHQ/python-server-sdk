# coding: utf-8

"""
    DevCycle Bucketing API

    Documents the DevCycle Bucketing API which provides and API interface to User Bucketing and for generated SDKs.  # noqa: E501
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from time import time


@dataclass(eq=False, order=False)
class Event:
    type: str
    target: Optional[str] = None
    date: int = field(default_factory=lambda: int(time()))
    value: Optional[int] = None
    metaData: Dict[str, str] = field(default_factory=dict)

    def to_json(self):
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None
        }
