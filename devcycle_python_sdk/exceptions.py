from typing import Optional


class CloudClientError(Exception):
    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.__cause__ = cause

    def __str__(self):
        return f"CloudClientException: {self.message}"


class CloudClientUnauthorizedError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(Exception):
    def __init__(self, key: str):
        self.key = key
