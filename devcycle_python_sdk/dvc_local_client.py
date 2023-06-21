import logging
import platform

from typing import Any, Dict

from devcycle_python_sdk import DevCycleLocalOptions
from devcycle_python_sdk.api.local_bucketing import LocalBucketing
from devcycle_python_sdk.managers.config_manager import EnvironmentConfigManager
from devcycle_python_sdk.managers.event_queue_manager import EventQueueManager
from devcycle_python_sdk.models.event import Event
from devcycle_python_sdk.models.feature import Feature
from devcycle_python_sdk.models.user import User
from devcycle_python_sdk.models.variable import Variable, determine_variable_type
from devcycle_python_sdk.util.version import sdk_version

import devcycle_python_sdk.protobuf.utils as pb_utils
import devcycle_python_sdk.protobuf.variableForUserParams_pb2 as pb2

logger = logging.getLogger(__name__)


class DevCycleLocalClient:
    def __init__(self, sdk_key: str, options: DevCycleLocalOptions):
        self._validate_sdk_key(sdk_key)
        self._sdk_key = sdk_key

        if options is None:
            self.options: DevCycleLocalOptions = DevCycleLocalOptions()
        else:
            self.options = options

        self.platform = "Python"
        self.platform_version = platform.python_version()
        self.sdk_version = sdk_version()
        self.sdk_type = "local"

        self.local_bucketing = LocalBucketing(sdk_key)
        self.config_manager: EnvironmentConfigManager = EnvironmentConfigManager(sdk_key, self.options,
                                                                                 self.local_bucketing)
        self.event_queue_manager: EventQueueManager = EventQueueManager(sdk_key, self.options, self.local_bucketing)

    def _add_platform_data_to_user(self, user: User) -> User:
        user.platform = self.platform
        user.platformVersion = self.platform_version
        user.sdkVersion = self.sdk_version
        user.sdkType = self.sdk_type
        return user

    def _validate_sdk_key(self, sdk_key: str) -> None:
        if sdk_key is None or len(sdk_key) == 0:
            raise ValueError("Missing SDK key! Call build with a valid server SDK key")

        if not sdk_key.startswith("server") and not sdk_key.startswith("dvc_server"):
            raise ValueError(
                "Invalid SDK key provided. Call build with a valid server SDK key"
            )

    def _validate_user(self, user: User) -> None:
        if user is None:
            raise ValueError("User cannot be None")

        if user.user_id is None or len(user.user_id) == 0:
            raise ValueError("userId cannot be empty")

    def _is_initialized(self) -> bool:
        return (self.config_manager and self.config_manager.is_initialized())

    def set_client_custom_data(self, custom_data: Dict[str, Any]) -> None:
        if not self._is_initialized():
            logger.debug("set_client_custom_data called before client has initialized")
            return

        # TODO delegate to local bucketing api
        pass

    def variable_value(self, user: User, key: str, default_value: Any) -> Any:
        return self.variable(user, key, default_value).value

    def variable(self, user: User, key: str, default_value: Any) -> Variable:

        self._validate_user(user)
        user = self._add_platform_data_to_user(user)

        if not key:
            raise ValueError("Missing parameter: key")

        if default_value is None:
            raise ValueError("Missing parameter: defaultValue")

        if not self._is_initialized():
            logger.debug("variable called before client has initialized")
            # TODO track aggregate event for default variable
            return Variable.create_default_variable(key, default_value)

        var_type = determine_variable_type(default_value)
        pb_variable_type = pb_utils.convert_type_enum_to_variable_type(var_type)

        params_pb = pb2.VariableForUserParams_PB(
            sdkKey=self._sdk_key,
            variableKey=key,
            variableType=pb_variable_type,
            user=pb_utils.convert_user_to_user_pb(user),
            shouldTrackEvent=True,
        )

        try:
            params_str = params_pb.SerializeToString()

            variable_data = self.local_bucketing.get_variable_for_user_protobuf(params_str)
            if variable_data is None or len(variable_data) == 0:
                return Variable.create_default_variable(key, default_value)
            else:
                sdk_variable_pb = pb2.SDKVariable_PB()
                sdk_variable_pb.ParseFromString(variable_data)

                if sdk_variable_pb.type != pb_variable_type:
                    logger.info("Variable type mismatch, returning default value")
                    return Variable.create_default_variable(key, default_value)

                return pb_utils.create_variable(sdk_variable_pb, default_value)
        except Exception as e:
            logger.error("Error retrieving variable for user: %s", e)
            return Variable.create_default_variable(key, default_value)

    def all_variables(self, user: User) -> Dict[str, Variable]:
        self._validate_user(user)
        user = self._add_platform_data_to_user(user)

        if not self._is_initialized():
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
        self._validate_user(user)
        user = self._add_platform_data_to_user(user)

        if not self._is_initialized():
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
        self._validate_user(user)
        user = self._add_platform_data_to_user(user)

        if user_event is None or not user_event.type:
            raise ValueError("Invalid Event")

        if not self._is_initialized():
            logger.debug("track called before client has initialized")
            return

        # events = [user_event]
        try:
            # TODO delegate to local bucketing api
            pass
        except Exception as e:
            logger.error("Error tracking event: %s", e)

    def close(self) -> None:
        if self.config_manager:
            self.config_manager.close()

        if self.event_queue_manager:
            self.event_queue_manager.close()
