# ruff: noqa: N815
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


@dataclass(order=False)
class DevCycleUser:
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    appVersion: Optional[str] = None
    appBuild: Optional[str] = None
    customData: Optional[Dict[str, str]] = None
    createdDate: datetime = field(default_factory=lambda: datetime.utcnow())
    privateCustomData: Optional[Dict[str, str]] = None
    lastSeenDate: Optional[datetime] = None
    platform: Optional[str] = None
    platformVersion: Optional[str] = None
    deviceModel: Optional[str] = None
    sdkType: Optional[str] = None
    sdkVersion: Optional[str] = None

    def to_json(self):
        json_dict = {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None
            and key not in ["createdDate", "lastSeenDate"]
        }

        if self.createdDate:
            json_dict["createdDate"] = self.createdDate.astimezone(
                tz=timezone.utc
            ).isoformat()
        if self.lastSeenDate:
            json_dict["lastSeenDate"] = self.lastSeenDate.astimezone(
                tz=timezone.utc
            ).isoformat()
        return json_dict

    @classmethod
    def from_json(cls, data: dict) -> "DevCycleUser":
        if "createdDate" in data:
            created_date = datetime.fromisoformat(
                data["createdDate"].replace("Z", "+00:00")
            )
        else:
            created_date = datetime.utcnow()

        last_seen_date = None
        if "lastSeenDate" in data:
            last_seen_date = datetime.fromisoformat(
                data["lastSeenDate"].replace("Z", "+00:00")
            )

        return cls(
            user_id=data["user_id"],
            email=data.get("email"),
            name=data.get("name"),
            language=data.get("language"),
            country=data.get("country"),
            appVersion=data.get("appVersion"),
            appBuild=data.get("appBuild"),
            customData=data.get("customData"),
            privateCustomData=data.get("privateCustomData"),
            createdDate=created_date,
            lastSeenDate=last_seen_date,
            platform=data.get("platform"),
            platformVersion=data.get("platformVersion"),
            deviceModel=data.get("deviceModel"),
            sdkType=data.get("sdkType"),
            sdkVersion=data.get("sdkVersion"),
        )
