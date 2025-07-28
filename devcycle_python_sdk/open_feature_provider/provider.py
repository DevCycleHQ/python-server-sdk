import logging
import time

from typing import Any, Optional, Union, List

from devcycle_python_sdk import AbstractDevCycleClient
from devcycle_python_sdk.models.user import DevCycleUser

from openfeature.provider import AbstractProvider
from openfeature.provider.metadata import Metadata
from openfeature.evaluation_context import EvaluationContext
from openfeature.flag_evaluation import FlagResolutionDetails, Reason
from openfeature.exception import (
    ErrorCode,
    InvalidContextError,
    TypeMismatchError,
    GeneralError,
)
from openfeature.hook import Hook

logger = logging.getLogger(__name__)


class DevCycleProvider(AbstractProvider):
    """
    Openfeature provider wrapper for the DevCycle SDK.

    Can be initialized with either a DevCycleLocalClient or DevCycleCloudClient instance.
    """

    def __init__(self, devcycle_client: AbstractDevCycleClient):
        self.client = devcycle_client
        self.meta_data = Metadata(name=f"DevCycle {self.client.get_sdk_platform()}")

    def initialize(self, evaluation_context: EvaluationContext) -> None:
        timeout = 2
        start_time = time.time()

        # Wait for the client to be initialized or timeout
        while not self.client.is_initialized():
            if time.time() - start_time > timeout:
                raise GeneralError(
                    f"DevCycleProvider initialization timed out after {timeout} seconds"
                )
            time.sleep(0.1)  # Sleep briefly to avoid busy waiting

        if self.client.is_initialized():
            logger.debug("DevCycleProvider initialized successfully")

    def shutdown(self) -> None:
        self.client.close()

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
                    # TODO: once eval enabled from cloud bucketing, eval reason won't be null unless defaulted
                    if variable.eval and variable.eval.reason:
                        reason = variable.eval.reason
                    elif variable.isDefaulted:
                        reason = Reason.DEFAULT
                    else:
                        reason = Reason.TARGETING_MATCH

                    return FlagResolutionDetails(
                        value=variable.value,
                        reason=reason,
                        flag_metadata=variable.get_flag_meta_data(),
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
