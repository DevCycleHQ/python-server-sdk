import typing
import logging

from devcycle_python_sdk import DevCycleLocalClient
from devcycle_python_sdk.models.user import DevCycleUser

from openfeature.provider.provider import AbstractProvider
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagResolutionDetails, Reason
from openfeature.exception import ErrorCode
from openfeature.hook import Hook
from openfeature.provider.metadata import Metadata

logger = logging.getLogger(__name__)


class UserDataError(Exception):
    pass


def _set_custom_value(custom_data: dict, key: str, value: typing.Optional[typing.Any]):
    if (
        custom_data is not None
        and key
        and value is not None
        and isinstance(value, (str, int, float, bool))
    ):
        custom_data[key] = value


def _create_user_from_context(context: EvaluationContext) -> DevCycleUser:
    user_id = None

    if context:
        if context.targeting_key:
            user_id = context.targeting_key
        elif context.attributes and "userId" in context.attributes.keys():
            user_id = context.attributes["userId"]

    if not user_id:
        raise UserDataError(
            "DevCycle: Evaluation context does not contain a targeting key or userId attribute"
        )

    user = DevCycleUser(user_id=user_id)
    custom_data = {}
    private_custom_data = {}
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

    if custom_data:
        user.customData = custom_data

    if private_custom_data:
        user.privateCustomData = private_custom_data

    return user


class DevCycleProvider(AbstractProvider):
    def __init__(self, devcycle_client: DevCycleLocalClient):
        self.client = devcycle_client
        self.meta_data = Metadata(name="DevCycle Provider")

    def get_metadata(self) -> Metadata:
        return self.meta_data

    def get_provider_hooks(self) -> typing.List[Hook]:
        return []

    def _resolve_details(
        self,
        flag_key: str,
        default_value: typing.Any,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[typing.Any]:
        if self.client.is_initialized():
            try:
                user: DevCycleUser = _create_user_from_context(evaluation_context)

                variable = self.client.variable(
                    key=flag_key, user=user, default_value=default_value
                )

                if variable is None:
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
                return FlagResolutionDetails(
                    value=default_value,
                    reason=Reason.ERROR,
                    error_code=ErrorCode.INVALID_CONTEXT,
                    error_message=str(e),
                )
            except UserDataError as e:
                return FlagResolutionDetails(
                    value=default_value,
                    reason=Reason.ERROR,
                    error_code=ErrorCode.TARGETING_KEY_MISSING,
                    error_message=str(e),
                )
            except Exception as e:
                return FlagResolutionDetails(
                    value=default_value,
                    reason=Reason.ERROR,
                    error_code=ErrorCode.PARSE_ERROR,
                    error_message=str(e),
                )
        else:
            logger.debug(
                "DevCycle: variable evaluation called before client has initialized"
            )
            return FlagResolutionDetails(
                value=default_value,
                reason=Reason.ERROR,
                error_code=ErrorCode.PROVIDER_NOT_READY,
            )

    def resolve_boolean_details(
        self,
        flag_key: str,
        default_value: bool,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[bool]:
        return self._resolve_details(flag_key, default_value, evaluation_context)

    def resolve_string_details(
        self,
        flag_key: str,
        default_value: str,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[str]:
        return self._resolve_details(flag_key, default_value, evaluation_context)

    def resolve_integer_details(
        self,
        flag_key: str,
        default_value: int,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[int]:
        return self._resolve_details(flag_key, default_value, evaluation_context)

    def resolve_float_details(
        self,
        flag_key: str,
        default_value: float,
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[float]:
        return self._resolve_details(flag_key, default_value, evaluation_context)

    def resolve_object_details(
        self,
        flag_key: str,
        default_value: typing.Union[dict, list],
        evaluation_context: typing.Optional[EvaluationContext] = None,
    ) -> FlagResolutionDetails[typing.Union[dict, list]]:
        return self._resolve_details(flag_key, default_value, evaluation_context)
