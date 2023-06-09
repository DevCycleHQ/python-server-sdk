from typing import Optional


class CloudClientException(Exception):
    def __init__(self, message: str, cause: Optional[Exception] = None):
        self.message = message
        self.__cause__ = cause


class NotFoundException(Exception):
    def __init__(self, key: str):
        self.key = key
