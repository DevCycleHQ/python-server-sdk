import logging

from typing import Any, Optional, Union, List

from devcycle_python_sdk import AbstractDevCycleClient
from devcycle_python_sdk.models.user import DevCycleUser

from openfeature.provider import AbstractProvider
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagResolutionDetails, Reason
from openfeature.exception import ErrorCode, InvalidContextError, TypeMismatchError
from openfeature.hook import Hook
from openfeature.provider.metadata import Metadata

logger = logging.getLogger(__name__)


class DevCycleProvider(AbstractProvider):
    """
    Openfeature provider wrapper for the DevCycle SDK.

    Can be initialized with either a DevCycleLocalClient or DevCycleCloudClient instance.
    """

    def __init__(self, devcycle_client: AbstractDevCycleClient):
        self.client = devcycle_client
        self.meta_data = Metadata(name=f"DevCycle {self.client.get_sdk_platform()}")

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
                user: DevCycleUser = DevCycleUser.create_user_from_context(
                    evaluation_context
                )

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
                        reason=(
                            Reason.DEFAULT
                            if variable.isDefaulted
                            else Reason.TARGETING_MATCH
                        ),
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
        if not isinstance(default_value, dict):
            raise TypeMismatchError("Default value must be a flat dictionary")

        if default_value:
            for k, v in default_value.items():
                if not isinstance(v, (str, int, float, bool)) or v is None:
                    raise TypeMismatchError(
                        "Default value must be a flat dictionary containing only strings, numbers, booleans or None values"
                    )

        return self._resolve(flag_key, default_value, evaluation_context)
