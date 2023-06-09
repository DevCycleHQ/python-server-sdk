from typing import Optional


class CloudClientException(Exception):
    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.__cause__ = cause

    def __str__(self):
        return f"CloudClientException: {self.message}"


class NotFoundException(Exception):
    def __init__(self, key: str):
        self.key = key
