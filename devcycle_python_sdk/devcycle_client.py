import typing
from abc import abstractmethod

from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.variable import Variable

from openfeature.provider import AbstractProvider


class AbstractDevCycleClient:
    """
    A common interface for all DevCycle Clients
    """

    @abstractmethod
    def is_initialized(self) -> bool:
        pass

    @abstractmethod
    def variable(
        self, user: DevCycleUser, key: str, default_value: typing.Any
    ) -> Variable:
        pass

    @abstractmethod
    def variable_value(
        self, user: DevCycleUser, key: str, default_value: typing.Any
    ) -> typing.Any:
        pass

    @abstractmethod
    def get_openfeature_provider(self) -> AbstractProvider:
        """
        Returns the OpenFeature provider for this client
        """
        pass

    @abstractmethod
    def get_sdk_platform(self) -> str:
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Closes the client and releases any resources held by it.
        """
        pass
