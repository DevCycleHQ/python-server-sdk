import logging
import platform

from typing import Any, Dict

from devcycle_python_sdk.exceptions import (
    NotFoundException,
    CloudClientUnauthorizedException,
)
from devcycle_python_sdk.models import Event, Feature, UserData, Variable
from devcycle_python_sdk.dvc_options import DVCCloudOptions
from devcycle_python_sdk.util.version import sdk_version
from devcycle_python_sdk.api.bucketing_client import BucketingAPIClient

logger = logging.getLogger(__name__)


class DVCCloudClient:
    options: DVCCloudOptions
    platform: str
    platform_version: str
    sdk_version: str

    def __init__(self, sdk_key: str, options: DVCCloudOptions):
        self._validate_sdk_key(sdk_key)

        if options is None:
            self.options = DVCCloudOptions()
        else:
            self.options = options

        self.platform = "Python"
        self.platform_version = platform.python_version()
        self.sdk_version = sdk_version()
        self.bucketing_api = BucketingAPIClient(sdk_key, self.options)

    def _add_platform_data_to_user(self, user: UserData) -> UserData:
        user.platform = self.platform
        user.platformVersion = self.platform_version
        user.sdkVersion = self.sdk_version
        return user

    def _validate_sdk_key(self, sdk_key: str) -> None:
        if sdk_key is None or len(sdk_key) == 0:
            raise ValueError("Missing SDK key! Call build with a valid SDK key")

        if not sdk_key.startswith("server") and not sdk_key.startswith("dvc_server"):
            raise ValueError(
                "Invalid SDK key provided. Please call build with a valid server SDK key"
            )

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

        if default_value is None:
            raise ValueError("Missing parameter: defaultValue")

        try:
            variable = self.bucketing_api.variable(key, user)
        except CloudClientUnauthorizedException as e:
            logger.warning("DevCycle: SDK key is invalid, unable to make cloud request")
            raise e
        except NotFoundException:
            logger.warning("DevCycle: variable not found: %s", key)
            return Variable.create_default_variable(
                key=key, default_value=default_value
            )
        except Exception as e:
            logger.error("DevCycle: Error fetching variable: %s", e)
            return Variable.create_default_variable(
                key=key, default_value=default_value
            )

        variable.defaultValue = default_value

        # Allow default value to be a subclass of the same type as the variable
        if not isinstance(default_value, type(variable.value)):
            logger.warning(
                "DevCycle: variable %s is type %s, but default value is type %s",
                key,
                type(variable.value),
                type(default_value),
            )
            return Variable.create_default_variable(
                key=key, default_value=default_value
            )

        return variable

    def all_variables(self, user: UserData) -> Dict[str, Variable]:
        self._validate_user(user)
        user = self._add_platform_data_to_user(user)

        variable_map: Dict[str, Variable] = {}
        try:
            variable_map = self.bucketing_api.variables(user)
        except CloudClientUnauthorizedException as e:
            logger.warning("DevCycle: SDK key is invalid, unable to make cloud request")
            raise e
        except Exception as e:
            logger.error("Error retrieving all features for a user: %s", e)

        return variable_map

    def all_features(self, user: UserData) -> Dict[str, Feature]:
        self._validate_user(user)
        user = self._add_platform_data_to_user(user)

        feature_map: Dict[str, Feature] = {}
        try:
            feature_map = self.bucketing_api.features(user)
        except CloudClientUnauthorizedException as e:
            logger.warning("DevCycle: SDK key is invalid, unable to make cloud request")
            raise e
        except Exception as e:
            logger.error("Error retrieving all features for a user: %s", e)

        return feature_map

    def track(self, user: UserData, user_event: Event) -> None:
        self._validate_user(user)
        user = self._add_platform_data_to_user(user)

        if user_event is None or not user_event.type:
            raise ValueError("Invalid Event")

        events = [user_event]
        try:
            self.bucketing_api.track(user, events)
        except CloudClientUnauthorizedException as e:
            logger.warning("DevCycle: SDK key is invalid, unable to make cloud request")
            raise e
        except Exception as e:
            logger.error("Error tracking event: %s", e)
