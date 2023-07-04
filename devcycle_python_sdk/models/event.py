# ruff: noqa: N815
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone

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
    date: datetime = field(default_factory=lambda: datetime.utcnow())
    value: Optional[int] = None
    metaData: Optional[Dict[str, str]] = None

    def to_json(self, use_bucketing_api_format: bool = False) -> Dict[str, Any]:
        json_dict = {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None and key != "date"
        }
        if self.date:
            if use_bucketing_api_format:
                # convert to timestamp in milliseconds as required by the bucketing API
                json_dict["date"] = int(self.date.timestamp() * 1000)
            else:
                # convert to UTC and format as ISO string
                json_dict["date"] = self.date.astimezone(tz=timezone.utc).isoformat()
        return json_dict


@dataclass(order=False)
class RequestEvent:
    """
    An event generated by local bucketing event that can be sent to the Events API
    Not interfaced by developers, purely for internal use
    """

    type: str
    user_id: str
    # will be a timestamp in iso format
    clientDate: str
    # will be a timestamp in iso format
    date: str
    target: Optional[str] = None
    customType: Optional[str] = None
    value: Optional[float] = 0
    featureVars: Dict[str, str] = field(default_factory=dict)
    metaData: Optional[Dict[str, str]] = None

    def to_json(self):
        json_obj = {}
        for key in self.__dataclass_fields__:
            json_obj[key] = getattr(self, key)

        return json_obj

    @classmethod
    def from_json(cls, data: dict) -> "RequestEvent":
        return cls(
            type=data["type"],
            user_id=data["user_id"],
            clientDate=data["clientDate"],
            date=data["date"],
            target=data.get("target"),
            customType=data.get("customType"),
            value=data.get("value", 0),
            featureVars=data.get("featureVars", {}),
            metaData=data.get("metaData"),
        )


@dataclass()
class UserEventsBatchRecord:
    """
    A collection of events generated by local bucketing library for a single user
    """

    user: User
    events: List[RequestEvent]

    def to_json(self) -> Dict[str, Any]:
        return {
            "user": self.user.to_json(),
            "events": [event.to_json() for event in self.events],
        }

    @classmethod
    def from_json(cls, data: dict) -> "UserEventsBatchRecord":
        return cls(
            user=User.from_json(data["user"]),
            events=[RequestEvent.from_json(element) for element in data["events"]],
        )


@dataclass()
class FlushPayload:
    """
    A collection of events exported by the local bucketing library that can be sent to the Events API as a batch
    """

    payloadId: str
    records: List[UserEventsBatchRecord]
    eventCount: int

    @classmethod
    def from_json(cls, data: dict) -> "FlushPayload":
        return cls(
            payloadId=data["payloadId"],
            eventCount=data["eventCount"],
            records=[
                UserEventsBatchRecord.from_json(element) for element in data["records"]
            ],
        )
