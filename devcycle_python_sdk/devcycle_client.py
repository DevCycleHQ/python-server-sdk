import typing
from abc import abstractmethod

from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.variable import Variable


class AbstractDevCycleClient:
    """
    A common interface for all DevCycle Clients
    """

    @abstractmethod
    def is_initialized(self) -> bool:
        pass

    def variable(
        self, key: str, user: DevCycleUser, default_value: typing.Any
    ) -> Variable:
        pass

    def variable_value(
        self, user: DevCycleUser, key: str, default_value: typing.Any
    ) -> typing.Any:
        pass
