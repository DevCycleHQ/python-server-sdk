# ruff: noqa: N815
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
import time
import datetime

from .user import User


class EventType:
    VariableEvaluated = "variableEvaluated"
    AggVariableEvaluated = "aggVariableEvaluated"
    VariableDefaulted = "variableDefaulted"
    AggVariableDefaulted = "aggVariableDefaulted"
    CustomEvent = "customEvent"


@dataclass(order=False)
class Event:
    type: Optional[str] = None
    target: Optional[str] = None
    date: int = field(default_factory=lambda: int(time.time()))
    value: Optional[int] = None
    metaData: Dict[str, str] = field(default_factory=dict)

    def to_json(self):
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None
        }


@dataclass(order=False)
class RequestEvent:
    type: str
    user_id: str
    clientDate: float
    date: float = field(default_factory=lambda: time.time())
    target: Optional[str] = None
    customType: Optional[str] = None
    value: Optional[int] = None
    featureVars: Dict[str, str]= field(default_factory=dict)
    metaData: Dict[str, str] = field(default_factory=dict)

    def to_json(self):
        json_obj = {}
        for key in self.__dataclass_fields__:
            if key == "date" or key == "clientDate":
                # timestamp needs to be converted to yyyy-MM-dd'T'hh:mm:ss.SSS'Z' format
                json_date = datetime.datetime.fromtimestamp(getattr(self, key))
                json_obj[key] = f"{json_date.isoformat()}Z"
            else:
                json_obj[key] = getattr(self, key)

        return json_obj

@dataclass()
class UserEventsBatchRecord:
    user: User
    events: list[RequestEvent]
    def to_json(self) -> Dict[str, Any]:
        return {
            "user": self.user.to_json(),
            "events": [event.to_json() for event in self.events],
        }

@dataclass(order=False)
class FlushPayload:
    payloadId: str
    records: list[UserEventsBatchRecord]
    eventCount: int


