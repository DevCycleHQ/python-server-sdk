import logging
import platform

from typing import Any, Dict

from devcycle_python_sdk import DevCycleCloudOptions, AbstractDevCycleClient
from devcycle_python_sdk.api.bucketing_client import BucketingAPIClient
from devcycle_python_sdk.exceptions import (
    NotFoundError,
    CloudClientUnauthorizedError,
)
from devcycle_python_sdk.managers.eval_hooks_manager import (
    EvalHooksManager,
    BeforeHookError,
    AfterHookError,
)
from devcycle_python_sdk.models.eval_reason import (
    DefaultReasonDetails,
)
from devcycle_python_sdk.models.eval_hook import EvalHook
from devcycle_python_sdk.models.eval_hook_context import HookContext
from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.event import DevCycleEvent
from devcycle_python_sdk.models.variable import Variable
from devcycle_python_sdk.models.feature import Feature
from devcycle_python_sdk.util.version import sdk_version
from devcycle_python_sdk.open_feature_provider.provider import DevCycleProvider

from openfeature.provider import AbstractProvider

logger = logging.getLogger(__name__)


class DevCycleCloudClient(AbstractDevCycleClient):
    """
    The DevCycle Python SDK that utilizes the DevCycle Bucketing API for feature and variable evaluation
    """

    options: DevCycleCloudOptions
    platform: str
    platform_version: str
    sdk_version: str

    def __init__(self, sdk_key: str, options: DevCycleCloudOptions):
        _validate_sdk_key(sdk_key)

        if options is None:
            self.options = DevCycleCloudOptions()
        else:
            self.options = options

        self.platform = "Python"
        self.platform_version = platform.python_version()
        self.sdk_version = sdk_version()
        self.sdk_type = "server"
        self.bucketing_api = BucketingAPIClient(sdk_key, self.options)
        self._openfeature_provider = DevCycleProvider(self)
        self.eval_hooks_manager = EvalHooksManager(
            None if options is None else options.eval_hooks
        )

    def get_sdk_platform(self) -> str:
        return "Cloud"

    def get_openfeature_provider(self) -> AbstractProvider:
        return self._openfeature_provider

    def _add_platform_data_to_user(self, user: DevCycleUser) -> DevCycleUser:
        user.platform = self.platform
        user.platformVersion = self.platform_version
        user.sdkVersion = self.sdk_version
        user.sdkType = self.sdk_type
        return user

    def is_initialized(self) -> bool:
        return True

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
        user = self._add_platform_data_to_user(user)

        if not key:
            raise ValueError("Missing parameter: key")

        if default_value is None:
            raise ValueError("Missing parameter: defaultValue")

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
            variable = self.bucketing_api.variable(key, context.user)
            if before_hook_error is None:
                self.eval_hooks_manager.run_after(context, variable)
            else:
                raise before_hook_error
        except CloudClientUnauthorizedError as e:
            logger.warning("DevCycle: SDK key is invalid, unable to make cloud request")
            raise e
        except NotFoundError:
            logger.warning(f"DevCycle: Variable not found: {key}")
            return Variable.create_default_variable(
                key=key,
                default_value=default_value,
                default_reason_detail=DefaultReasonDetails.MISSING_VARIABLE,
            )
        except BeforeHookError as e:
            self.eval_hooks_manager.run_error(context, e)
        except AfterHookError as e:
            self.eval_hooks_manager.run_error(context, e)
        except Exception as e:
            logger.error(f"DevCycle: Error evaluating variable: {e}")
            return Variable.create_default_variable(
                key=key,
                default_value=default_value,
                default_reason_detail=DefaultReasonDetails.ERROR,
            )
        finally:
            self.eval_hooks_manager.run_finally(context, variable)

        variable.defaultValue = default_value

        # Allow default value to be a subclass of the same type as the variable
        if not isinstance(default_value, type(variable.value)):
            logger.warning(
                f"DevCycle: Variable {key} is type {type(variable.value)}, but default value is type {type(default_value)}",
            )
            return Variable.create_default_variable(
                key=key,
                default_value=default_value,
                default_reason_detail=DefaultReasonDetails.TYPE_MISMATCH,
            )

        return variable

    def all_variables(self, user: DevCycleUser) -> Dict[str, Variable]:
        """
        Returns all segmented and bucketed variables for a user.  This method will return an empty map if the user is not bucketed into any variables

        :param user: The user to retrieve features for
        """
        _validate_user(user)
        user = self._add_platform_data_to_user(user)

        variable_map: Dict[str, Variable] = {}
        try:
            variable_map = self.bucketing_api.variables(user)
        except CloudClientUnauthorizedError as e:
            logger.warning("DevCycle: SDK key is invalid, unable to make cloud request")
            raise e
        except Exception as e:
            logger.error(f"DevCycle: Error retrieving all features for a user: {e}")

        return variable_map

    def all_features(self, user: DevCycleUser) -> Dict[str, Feature]:
        """
        Returns all segmented and bucketed features for a user.  This method will return an empty map if the user is not bucketed into any features

        :param user: The user to retrieve features for
        """
        _validate_user(user)
        user = self._add_platform_data_to_user(user)

        feature_map: Dict[str, Feature] = {}
        try:
            feature_map = self.bucketing_api.features(user)
        except CloudClientUnauthorizedError as e:
            logger.warning("DevCycle: SDK key is invalid, unable to make cloud request")
            raise e
        except Exception as e:
            logger.error(f"DevCycle: Error retrieving all features for a user: {e}")

        return feature_map

    def track(self, user: DevCycleUser, user_event: DevCycleEvent) -> None:
        """
        Tracks a custom event for a user.

        :param user: The user to track the event for
        :param user_event: The event to track
        """

        if user_event is None or not user_event.type:
            raise ValueError("Invalid Event")

        _validate_user(user)
        user = self._add_platform_data_to_user(user)

        if user_event is None or not user_event.type:
            raise ValueError("Invalid Event")

        events = [user_event]
        try:
            self.bucketing_api.track(user, events)
        except CloudClientUnauthorizedError as e:
            logger.warning("DevCycle: SDK key is invalid, unable to make cloud request")
            raise e
        except Exception as e:
            logger.error(f"DevCycle: Error tracking event: {e}")

    def close(self) -> None:
        """
        Closes the client and releases any resources held by it.
        """
        # Cloud client doesn't need to release any resources
        logger.debug("DevCycle: Cloud client closed")

    def add_hook(self, hook: EvalHook) -> None:
        self.eval_hooks_manager.add_hook(hook)

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
