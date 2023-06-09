from typing import Optional


class CloudClientException(Exception):
    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.__cause__ = cause

    def __str__(self):
        return f"CloudClientException: {self.message}"


class CloudClientUnauthorizedException(Exception):
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message, cause)


class NotFoundException(Exception):
    def __init__(self, key: str):
        self.key = key
