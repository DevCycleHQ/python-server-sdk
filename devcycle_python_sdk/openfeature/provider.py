import logging

from typing import Any, Dict, Optional, Union, List

from devcycle_python_sdk import AbstractDevCycleClient
from devcycle_python_sdk.models.user import DevCycleUser

from openfeature.provider.provider import AbstractProvider
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagResolutionDetails, Reason
from openfeature.exception import (
    ErrorCode,
    TargetingKeyMissingError,
    InvalidContextError,
)
from openfeature.hook import Hook
from openfeature.provider.metadata import Metadata

logger = logging.getLogger(__name__)


def _set_custom_value(custom_data: Dict[str, Any], key: str, value: Optional[Any]):
    """
    Sets a custom value in the custom data dictionary.  Custom data properties can
    only be strings, numbers, or booleans.  Nested dictionaries and lists are
    not permitted.

    Invalid values are ignored
    """
    if (
        custom_data is not None
        and key
        and value is not None
        and isinstance(value, (str, int, float, bool))
    ):
        custom_data[key] = value


def _create_user_from_context(context: EvaluationContext) -> DevCycleUser:
    """
    Builds a DevCycleUser instance from the evaluation context. Will raise a TargetingKeyMissingError if
    the context does not contain a valid targeting key or user_id attribute

    :param context: The evaluation context to build the user from
    :return: A DevCycleUser instance
    """
    user_id = None

    if context:
        if context.targeting_key:
            user_id = context.targeting_key
        elif context.attributes and "user_id" in context.attributes.keys():
            user_id = context.attributes["user_id"]

    if not user_id:
        raise TargetingKeyMissingError(
            "DevCycle: Evaluation context does not contain a valid targeting key or user_id attribute"
        )

    user = DevCycleUser(user_id=user_id)
    custom_data: Dict[str, str] = {}
    private_custom_data: Dict[str, str] = {}
    if context and context.attributes:
        for key, value in context.attributes.items():
            if value:
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
                        _set_custom_value(custom_data, k, v)
                elif key == "privateCustomData" and isinstance(value, dict):
                    for k, v in value.items():
                        _set_custom_value(private_custom_data, k, v)
                else:
                    # unrecognized keys are just added to public custom data
                    _set_custom_value(custom_data, key, value)

    if custom_data:
        user.customData = custom_data

    if private_custom_data:
        user.privateCustomData = private_custom_data

    return user


class DevCycleProvider(AbstractProvider):
    """
    Openfeature provider wrapper for the DevCycle SDK.

    Can be initialized with either a DevCycleLocalClient or DevCycleCloudClient instance.
    """

    def __init__(self, devcycle_client: AbstractDevCycleClient):
        self.client = devcycle_client
        self.meta_data = Metadata(name="DevCycle Provider")

    def get_metadata(self) -> Metadata:
        return self.meta_data

    def get_provider_hooks(self) -> List[Hook]:
        return []

    def _resolve(
        self,
        flag_key: str,
        default_value: Any,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[Any]:
        if self.client.is_initialized():
            try:
                user: DevCycleUser = _create_user_from_context(evaluation_context)

                variable = self.client.variable(
                    key=flag_key, user=user, default_value=default_value
                )

                if variable is None:
                    # this technically should never happen
                    # as the DevCycle client should at least return a default Variable instance
                    return FlagResolutionDetails(
                        value=default_value,
                        reason=Reason.DEFAULT,
                    )
                else:
                    return FlagResolutionDetails(
                        value=variable.value,
                        reason=Reason.DEFAULT
                        if variable.isDefaulted
                        else Reason.TARGETING_MATCH,
                    )
            except ValueError as e:
                # occurs if the key or default value is None
                raise InvalidContextError(str(e))
        else:
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.ERROR,
                error_code=ErrorCode.PROVIDER_NOT_READY,
            )

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        return self._resolve(flag_key, default_value, evaluation_context)

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        return self._resolve(flag_key, default_value, evaluation_context)

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        return self._resolve(flag_key, default_value, evaluation_context)

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        return self._resolve(flag_key, default_value, evaluation_context)

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: Union[dict, list],
        evaluation_context: Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[Union[dict, list]]:
        return self._resolve(flag_key, default_value, evaluation_context)
