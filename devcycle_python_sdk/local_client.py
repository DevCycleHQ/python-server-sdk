import json
import logging
import uuid
from numbers import Real
from typing import Any, Dict, Union, Optional

from devcycle_python_sdk import DevCycleLocalOptions, AbstractDevCycleClient
from devcycle_python_sdk.api.local_bucketing import LocalBucketing
from devcycle_python_sdk.managers.config_manager import EnvironmentConfigManager
from devcycle_python_sdk.managers.eval_hooks_manager import (
    EvalHooksManager,
    BeforeHookError,
    AfterHookError,
)
from devcycle_python_sdk.managers.event_queue_manager import EventQueueManager
from devcycle_python_sdk.models.bucketed_config import BucketedConfig
from devcycle_python_sdk.models.eval_hook import EvalHook
from devcycle_python_sdk.models.eval_hook_context import HookContext
from devcycle_python_sdk.models.eval_reason import (
    DefaultReasonDetails,
    EvalReason,
    EvalReasons,
)
from devcycle_python_sdk.models.event import DevCycleEvent, EventType
from devcycle_python_sdk.models.feature import Feature
from devcycle_python_sdk.models.platform_data import default_platform_data
from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.variable import Variable
from devcycle_python_sdk.open_feature_provider.provider import DevCycleProvider
from openfeature.provider import AbstractProvider

logger = logging.getLogger(__name__)


class DevCycleLocalClient(AbstractDevCycleClient):
    """
    The DevCycle Python SDK that utilizes the local bucketing library for feature and variable evaluation
    """

    def __init__(self, sdk_key: str, options: DevCycleLocalOptions):
        _validate_sdk_key(sdk_key)
        self._sdk_key = sdk_key
        self.client_uuid = str(uuid.uuid4())

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
            sdk_key, self.client_uuid, self.options, self.local_bucketing
        )

        self._openfeature_provider: Optional[DevCycleProvider] = None
        self.eval_hooks_manager = EvalHooksManager(self.options.eval_hooks)

    def get_sdk_platform(self) -> str:
        return "Local"

    def get_openfeature_provider(self) -> AbstractProvider:
        if self._openfeature_provider is None:
            self._openfeature_provider = DevCycleProvider(self)

            # Update platform data for OpenFeature
            self._platform_data.sdkPlatform = "python-of"
            self.local_bucketing.set_platform_data(
                json.dumps(self._platform_data.to_json())
            )

        return self._openfeature_provider

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
            logger.debug(
                "DevCycle: set_client_custom_data called before client has initialized"
            )
            return

        if custom_data:
            try:
                custom_data_json = json.dumps(custom_data)
                self.local_bucketing.set_client_custom_data(custom_data_json)
            except Exception as e:
                logger.error("DevCycle: Error setting custom data: " + str(e))

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
            logger.debug("DevCycle: variable called before client has initialized")
            try:
                self.event_queue_manager.queue_aggregate_event(
                    event=DevCycleEvent(
                        type=EventType.AggVariableDefaulted,
                        target=key,
                        value=1,
                        metaData={"evalReason": EvalReasons.DEFAULT},
                    ),
                    bucketed_config=None,
                )
            except Exception as e:
                logger.warning(
                    f"DevCycle: Unable to track AggVariableDefaulted event for Variable {key}: {e}"
                )
            return Variable.create_default_variable(
                key, default_value, DefaultReasonDetails.MISSING_CONFIG
            )

        context = HookContext(key, user, default_value)
        variable = Variable.create_default_variable(
            key=key, default_value=default_value
        )

        try:
            before_hook_error = None
            try:
                changed_context = self.eval_hooks_manager.run_before(context)
                if changed_context is not None:
                    context = changed_context
            except BeforeHookError as e:
                before_hook_error = e
            bucketed_variable = self.local_bucketing.get_variable_for_user_protobuf(
                user, key, default_value
            )
            if bucketed_variable is not None:
                variable = bucketed_variable
            else:
                variable.eval = EvalReason(
                    reason=EvalReasons.DEFAULT,
                    details=DefaultReasonDetails.USER_NOT_TARGETED,
                )

            if before_hook_error is None:
                self.eval_hooks_manager.run_after(context, variable)
            else:
                raise before_hook_error
        except Exception as e:
            variable.eval = EvalReason(
                reason=EvalReasons.DEFAULT, details=DefaultReasonDetails.ERROR
            )

            if isinstance(e, BeforeHookError):
                self.eval_hooks_manager.run_error(context, e)
            elif isinstance(e, AfterHookError):
                self.eval_hooks_manager.run_error(context, e)
            else:
                logger.warning(f"DevCycle: Error retrieving variable for user: {e}")

            return variable
        finally:
            self.eval_hooks_manager.run_finally(context, variable)
        return variable

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
            logger.warning(
                "DevCycle: all_variables called before client has initialized"
            )
            return {}

        try:
            return self.local_bucketing.generate_bucketed_config(user).variables
        except Exception as e:
            logger.exception(
                f"DevCycle: Error retrieving all variables for a user: {e}"
            )
            return {}

    def all_features(self, user: DevCycleUser) -> Dict[str, Feature]:
        """
        Returns all segmented and bucketed features for a user.  This method will return an empty map if the client has not been initialized or if the user is not bucketed into any features

        :param user: The user to retrieve features for
        """
        _validate_user(user)

        if not self.is_initialized():
            logger.warning(
                "DevCycle: all_features called before client has initialized"
            )
            return {}

        feature_map: Dict[str, Feature] = {}
        try:
            return self.local_bucketing.generate_bucketed_config(user).features
        except Exception as e:
            logger.exception(f"DevCycle: Error retrieving all features for a user: {e}")

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
            logger.debug("DevCycle: track called before client has initialized")
            return

        try:
            self.event_queue_manager.queue_event(user, user_event)
        except Exception as e:
            logger.error(f"DevCycle: Error tracking event: {e}")

    def close(self) -> None:
        """
        Closes the client and releases any resources held by it.
        """
        self.config_manager.close()
        self.event_queue_manager.close()

    def add_hook(self, eval_hook: EvalHook) -> None:
        self.eval_hooks_manager.add_hook(eval_hook)

    def clear_hooks(self) -> None:
        self.eval_hooks_manager.clear_hooks()


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
