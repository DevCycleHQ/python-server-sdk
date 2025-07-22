# ruff: noqa: N815
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from openfeature.evaluation_context import EvaluationContext
from openfeature.exception import TargetingKeyMissingError, InvalidContextError


@dataclass(order=False)
class DevCycleUser:
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    appVersion: Optional[str] = None
    appBuild: Optional[str] = None
    customData: Optional[Dict[str, Any]] = None
    createdDate: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    privateCustomData: Optional[Dict[str, Any]] = None
    lastSeenDate: Optional[datetime] = None
    platform: Optional[str] = None
    platformVersion: Optional[str] = None
    deviceModel: Optional[str] = None
    sdkType: Optional[str] = None
    sdkVersion: Optional[str] = None
    sdkPlatform: Optional[str] = None

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
            created_date = datetime.now(timezone.utc)

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
            sdkPlatform=data.get("sdkPlatform"),
        )

    @staticmethod
    def _set_custom_value(custom_data: Dict[str, Any], key: str, value: Optional[Any]):
        """
        Sets a custom value in the custom data dictionary.  Custom data properties can
        only be strings, numbers, or booleans.  Nested dictionaries and lists are
        not permitted.

        Invalid values will generate an error
        """
        if key and (value is None or isinstance(value, (str, int, float, bool))):
            custom_data[key] = value
        else:
            raise InvalidContextError(
                "Custom property values must be strings, numbers, booleans or None"
            )

    @staticmethod
    def create_user_from_context(
        context: Optional[EvaluationContext],
    ) -> "DevCycleUser":
        """
        Builds a DevCycleUser instance from the evaluation context. Will raise a TargetingKeyMissingError if
        the context does not contain a valid targeting key, user_id, or userId attribute

        :param context: The evaluation context to build the user from
        :return: A DevCycleUser instance
        """
        user_id = None
        user_id_source = None

        if context:
            if context.targeting_key:
                user_id = context.targeting_key
                user_id_source = "targeting_key"
            elif context.attributes and "user_id" in context.attributes.keys():
                user_id = context.attributes["user_id"]
                user_id_source = "user_id"
            elif context.attributes and "userId" in context.attributes.keys():
                user_id = context.attributes["userId"]
                user_id_source = "userId"

        if not user_id:
            raise TargetingKeyMissingError(
                "DevCycle: Evaluation context does not contain a valid targeting key, user_id, or userId attribute"
            )

        if not isinstance(user_id, str):
            raise TargetingKeyMissingError(
                f"DevCycle: {user_id_source} must be a string, got {type(user_id).__name__}"
            )

        user = DevCycleUser(user_id=user_id)
        custom_data: Dict[str, Any] = {}
        private_custom_data: Dict[str, Any] = {}
        if context and context.attributes:
            for key, value in context.attributes.items():
                # Skip user_id, userId, and targeting_key - these are reserved for user ID mapping
                if key in ("user_id", "userId", "targeting_key"):
                    continue

                if value is not None:
                    if key == "email" and isinstance(value, str):
                        user.email = value
                    elif key == "name" and isinstance(value, str):
                        user.name = value
                    elif key == "language" and isinstance(value, str):
                        user.language = value
                    elif key == "country" and isinstance(value, str):
                        user.country = value
                    elif key == "appVersion" and isinstance(value, str):
                        user.appVersion = value
                    elif key == "appBuild" and isinstance(value, str):
                        user.appBuild = value
                    elif key == "deviceModel" and isinstance(value, str):
                        user.deviceModel = value
                    elif key == "customData" and isinstance(value, dict):
                        for k, v in value.items():
                            DevCycleUser._set_custom_value(custom_data, k, v)
                    elif key == "privateCustomData" and isinstance(value, dict):
                        for k, v in value.items():
                            DevCycleUser._set_custom_value(private_custom_data, k, v)
                    else:
                        # unrecognized keys are just added to public custom data
                        DevCycleUser._set_custom_value(custom_data, key, value)

        if custom_data:
            user.customData = custom_data

        if private_custom_data:
            user.privateCustomData = private_custom_data

        user.sdkPlatform = "python-of"
        return user
