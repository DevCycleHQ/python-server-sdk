from typing import Optional


class APIClientError(Exception):
    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.__cause__ = cause

    def __str__(self):
        return f"APIClientError: {self.message}"


class APIClientUnauthorizedError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class CloudClientError(APIClientError):
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message, cause)

    def __str__(self):
        return f"CloudClientException: {self.message}"


class CloudClientUnauthorizedError(APIClientUnauthorizedError):
    def __init__(self, message: str):
        super().__init__(message)


class NotFoundError(Exception):
    def __init__(self, key: str):
        self.key = key


class VariableTypeMismatchError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class MalformedConfigError(Exception):
    pass
