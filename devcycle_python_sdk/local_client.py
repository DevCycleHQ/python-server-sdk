import json
import logging
from numbers import Real
from typing import Any, Dict, Union

from devcycle_python_sdk import DevCycleLocalOptions
from devcycle_python_sdk.api.local_bucketing import LocalBucketing
from devcycle_python_sdk.exceptions import VariableTypeMismatchError
from devcycle_python_sdk.managers.config_manager import EnvironmentConfigManager
from devcycle_python_sdk.managers.event_queue_manager import EventQueueManager
from devcycle_python_sdk.models.bucketed_config import BucketedConfig
from devcycle_python_sdk.models.event import DevCycleEvent, EventType
from devcycle_python_sdk.models.feature import Feature
from devcycle_python_sdk.models.platform_data import default_platform_data
from devcycle_python_sdk.models.user import DevCycleUser
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
        return self.config_manager.is_initialized()

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

    def variable_value(self, user: DevCycleUser, key: str, default_value: Any) -> Any:
        """
        Evaluates a variable for a user and returns the value.  If the user is not bucketed into the variable, the default value will be returned

        :param user: The user to evaluate the variable for
        """
        return self.variable(user, key, default_value).value

    def variable(self, user: DevCycleUser, key: str, default_value: Any) -> Variable:
        """
        Evaluates a variable for a user.

        :param user: The user to evaluate the variable for
        :param key: The key of the variable to evaluate
        :param default_value: The default value to return if the user is not bucketed into the variable
        """
        _validate_user(user)

        if not key:
            raise ValueError("Missing parameter: key")

        if default_value is None:
            raise ValueError("Missing parameter: defaultValue")

        if not self.is_initialized():
            logger.debug("variable called before client has initialized")
            try:
                self.event_queue_manager.queue_aggregate_event(
                    event=DevCycleEvent(
                        type=EventType.AggVariableDefaulted, target=key, value=1
                    ),
                    bucketed_config=None,
                )
            except Exception as e:
                logger.warning(
                    f"Unable to track AggVariableDefaulted event for Variable {key}: {e}"
                )
            return Variable.create_default_variable(key, default_value)

        try:
            variable = self.local_bucketing.get_variable_for_user_protobuf(
                user, key, default_value
            )
            if variable:
                return variable
        except VariableTypeMismatchError:
            logger.debug("Variable type mismatch, returning default value")
        except Exception as e:
            logger.warning(f"Error retrieving variable for user: {e}")

        return Variable.create_default_variable(key, default_value)

    def _generate_bucketed_config(self, user: DevCycleUser) -> BucketedConfig:
        """
        Generates a bucketed config for a user.  This method will return an empty config if the client has not been initialized or if the user is not bucketed into any features or variables
        """

        _validate_user(user)

        return self.local_bucketing.generate_bucketed_config(user)

    def all_variables(self, user: DevCycleUser) -> Dict[str, Variable]:
        """
        Returns all segmented and bucketed variables for a user.  This method will return an empty map if the client has not been initialized or if the user is not bucketed into any variables

        :param user: The user to retrieve variables for
        """
        _validate_user(user)

        if not self.is_initialized():
            logger.warning("all_variables called before client has initialized")
            return {}

        variable_map: Dict[str, Variable] = {}

        try:
            return self.local_bucketing.generate_bucketed_config(user).variables
        except Exception as e:
            logger.exception(f"Error retrieving all variables for a user: {e}")
            return {}

        return variable_map

    def all_features(self, user: DevCycleUser) -> Dict[str, Feature]:
        """
        Returns all segmented and bucketed features for a user.  This method will return an empty map if the client has not been initialized or if the user is not bucketed into any features

        :param user: The user to retrieve features for
        """
        _validate_user(user)

        if not self.is_initialized():
            logger.warning("all_features called before client has initialized")
            return {}

        feature_map: Dict[str, Feature] = {}
        try:
            return self.local_bucketing.generate_bucketed_config(user).features
        except Exception as e:
            logger.exception(f"Error retrieving all features for a user: {e}")

        return feature_map

    def track(self, user: DevCycleUser, user_event: DevCycleEvent) -> None:
        """
        Tracks a custom event for a user.  This method will return immediately and the event will be queued for processing in the background.  If the client has not been initialized, this method will return immediately and the event will be discarded.

        :param user: The user to track the event for
        :param user_event: The event to track
        """
        _validate_user(user)

        if user_event is None:
            raise ValueError("Invalid Event")

        if user_event.type is None or len(user_event.type) == 0:
            raise ValueError("Missing parameter: type")

        if not self.is_initialized():
            logger.debug("track called before client has initialized")
            return

        try:
            self.event_queue_manager.queue_event(user, user_event)
        except Exception as e:
            logger.error(f"Error tracking event: {e}")

    def close(self) -> None:
        """
        Closes the client and releases any resources held by it.
        """
        self.config_manager.close()
        self.event_queue_manager.close()


def _validate_sdk_key(sdk_key: str) -> None:
    if sdk_key is None or len(sdk_key) == 0:
        raise ValueError("Missing SDK key! Call initialize with a valid SDK key")

    if not sdk_key.startswith("server") and not sdk_key.startswith("dvc_server"):
        raise ValueError(
            "Invalid SDK key provided. Please call initialize with a valid server SDK key"
        )


def _validate_user(user: DevCycleUser) -> None:
    if user is None:
        raise ValueError("User cannot be None")

    if user.user_id is None or len(user.user_id) == 0:
        raise ValueError("userId cannot be empty")
