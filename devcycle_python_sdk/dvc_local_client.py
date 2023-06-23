import json
import logging
from numbers import Real
from typing import Any, Dict, Union

from devcycle_python_sdk import DevCycleLocalOptions
from devcycle_python_sdk.api.local_bucketing import LocalBucketing
from devcycle_python_sdk.exceptions import VariableTypeMismatchError
from devcycle_python_sdk.managers.config_manager import EnvironmentConfigManager
from devcycle_python_sdk.managers.event_queue_manager import EventQueueManager
from devcycle_python_sdk.models.event import Event
from devcycle_python_sdk.models.feature import Feature
from devcycle_python_sdk.models.platform_data import default_platform_data
from devcycle_python_sdk.models.user import User
from devcycle_python_sdk.models.variable import Variable

logger = logging.getLogger(__name__)


class DevCycleLocalClient:
    def __init__(self, sdk_key: str, options: DevCycleLocalOptions):
        _validate_sdk_key(sdk_key)
        self._sdk_key = sdk_key

        if options is None:
            self.options: DevCycleLocalOptions = DevCycleLocalOptions()
        else:
            self.options = options

        self.local_bucketing = LocalBucketing(sdk_key)

        self._platform_data = default_platform_data()
        self.local_bucketing.set_platform_data(
            json.dumps(self._platform_data.to_json())
        )

        self.config_manager: EnvironmentConfigManager = EnvironmentConfigManager(
            sdk_key, self.options, self.local_bucketing
        )
        self.event_queue_manager: EventQueueManager = EventQueueManager(
            sdk_key, self.options, self.local_bucketing
        )

    def is_initialized(self) -> bool:
        return self.config_manager and self.config_manager.is_initialized()

    def set_client_custom_data(
        self, custom_data: Dict[str, Union[str, Real, bool, None]]
    ) -> None:
        """
        Sets global custom data for this client. This data will be utilized in all segmentation and bucketing
        decisions. This data will be merged with any custom data set on the user object, with user data
        taking priority

        :param custom_data: Global data to set.  Supported values are strings, numbers, booleans. Nested dictionaries
        are not permitted
        """
        if not self.is_initialized():
            logger.debug("set_client_custom_data called before client has initialized")
            return

        if custom_data:
            try:
                custom_data_json = json.dumps(custom_data)
                self.local_bucketing.set_client_custom_data(custom_data_json)
            except Exception as e:
                logger.error("Error setting custom data: " + str(e))

    def variable_value(self, user: User, key: str, default_value: Any) -> Any:
        return self.variable(user, key, default_value).value

    def variable(self, user: User, key: str, default_value: Any) -> Variable:
        _validate_user(user)

        if not key:
            raise ValueError("Missing parameter: key")

        if default_value is None:
            raise ValueError("Missing parameter: defaultValue")

        if not self.is_initialized():
            logger.debug("variable called before client has initialized")
            # TODO track aggregate event for default variable
            # need event queue setup for this
            return Variable.create_default_variable(key, default_value)

        try:
            variable = self.local_bucketing.get_variable_for_user_protobuf(
                user, key, default_value
            )
            if variable:
                return variable
        except VariableTypeMismatchError:
            logger.info("Variable type mismatch, returning default value")
        except Exception as e:
            logger.error("Error retrieving variable for user: %s", e)

        return Variable.create_default_variable(key, default_value)

    def all_variables(self, user: User) -> Dict[str, Variable]:
        _validate_user(user)

        if not self.is_initialized():
            logger.debug("all_variables called before client has initialized")
            return {}

        variable_map: Dict[str, Variable] = {}

        try:
            # TODO delegate to local bucketing api
            pass
        except Exception as e:
            logger.error("Error retrieving all features for a user: %s", e)

        return variable_map

    def all_features(self, user: User) -> Dict[str, Feature]:
        _validate_user(user)

        if not self.is_initialized():
            logger.debug("all_features called before client has initialized")
            return {}

        feature_map: Dict[str, Feature] = {}
        try:
            # TODO delegate to local bucketing api
            pass
        except Exception as e:
            logger.error("Error retrieving all features for a user: %s", e)

        return feature_map

    def track(self, user: User, user_event: Event) -> None:
        _validate_user(user)

        if user_event is None or not user_event.type:
            raise ValueError("Invalid Event")

        if not self.is_initialized():
            logger.debug("track called before client has initialized")
            return

        # events = [user_event]
        try:
            # TODO delegate to local bucketing api
            pass
        except Exception as e:
            logger.error("Error tracking event: %s", e)

    def close(self) -> None:
        """
        Closes the client and releases any resources held by it.
        """
        if self.config_manager:
            self.config_manager.close()

        if self.event_queue_manager:
            self.event_queue_manager.close()


def _validate_sdk_key(sdk_key: str) -> None:
    if sdk_key is None or len(sdk_key) == 0:
        raise ValueError("Missing SDK key! Call build with a valid server SDK key")

    if not sdk_key.startswith("server") and not sdk_key.startswith("dvc_server"):
        raise ValueError(
            "Invalid SDK key provided. Call build with a valid server SDK key"
        )


def _validate_user(user: User) -> None:
    if user is None:
        raise ValueError("User cannot be None")

    if user.user_id is None or len(user.user_id) == 0:
        raise ValueError("userId cannot be empty")
