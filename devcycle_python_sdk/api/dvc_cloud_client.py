import logging
import sys

from typing import Any

from devcycle_python_sdk.models.feature import Feature
from devcycle_python_sdk.models.user_data import UserData
from devcycle_python_sdk.models.variable import Variable
from devcycle_python_sdk.models.event import Event
from devcycle_python_sdk.dvc_options import DVCCloudOptions
from devcycle_python_sdk.util.version import sdk_version

logger = logging.getLogger(__name__)


class DVCCloudClient:

    def __init__(self, sdk_key: str, options: DVCCloudOptions):
        self._validate_sdk_key(sdk_key)

        if options is None:
            self.options = DVCCloudOptions()
        else:
            self.options = options

        self.platform = "Cloud"
        self.platform_version = sys.version
        self.sdk_version = sdk_version()

    def _add_platform_data_to_user(self, user: UserData) -> UserData:
        user.platform = self.platform
        user.platform_version = self.platform_version
        user.sdk_version = self.sdk_version
        return user

    def _validate_sdk_key(self, sdk_key: str) -> None:
        if sdk_key is None or len(sdk_key) == 0:
            raise ValueError("Missing SDK key! Call build with a valid SDK key")

        if not sdk_key.startswith("server") and not sdk_key.startswith("dvc_server"):
            raise ValueError("Invalid SDK key provided. Please call build with a valid server SDK key")

    def _validate_user(self, user: UserData) -> None:
        if user is None:
            raise ValueError("User cannot be None")

        if user.user_id is None or len(user.user_id) == 0:
            raise ValueError("userId cannot be empty")

    def variable_value(self, user: UserData, key: str, default_value: Any) -> Any:
        return self.variable(user, key, default_value).value

    def variable(self, user: UserData, key: str, default_value: Any) -> Variable:
        self._validate_user(user)
        user = self._add_platform_data_to_user(user)

        if not key:
            raise ValueError("Missing parameter: key")

        if not default_value:
            raise ValueError("Missing parameter: defaultValue")

        variable: Variable = None
        try:
            # do the API call here and replace the defaulted value
            return Variable(key=key, value=default_value, is_defaulted=True)
            pass
        except Exception as e:
            logger.error("Error fetching variable: %s", e)
            return Variable(key=key, value=default_value, is_defaulted=True)

    def all_variables(self, user: UserData) -> dict[str, Variable]:
        self._validate_user(user)
        user = self._add_platform_data_to_user(user)

        variable_map: dict[str, Variable] = {}
        try:
            # do the API call here
            pass
        except Exception as e:
            logger.error("Error retrieving all features for a user: %s", e)

        return variable_map

    def all_features(self, user: UserData) -> dict[str, Feature]:

        self._validate_user(user)
        user = self._add_platform_data_to_user(user)

        feature_map: dict[str, Feature] = {}
        try:
            # do the API call here
            pass
        except Exception as e:
            logger.error("Error retrieving all features for a user: %s", e)

        return feature_map

    def track(self, user: UserData, user_event: Event) -> None:
        self._validate_user(user)
        user = self._add_platform_data_to_user(user)

        if user_event is None or not user_event.type:
            raise ValueError("Invalid Event")

        events: list[Event] = [user_event]

        try:
            # do the API call here
            pass
        except Exception as e:
            logger.error("Error tracking event: %s", e)
