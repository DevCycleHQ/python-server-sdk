import logging
import math
from os.path import join
import random
import time
from typing import Dict, List, Optional

import requests

from devcycle_python_sdk.exceptions import CloudClientException, NotFoundException
from devcycle_python_sdk.dvc_options import DVCCloudOptions
from devcycle_python_sdk.models import Variable, UserData, Feature, Event

logger = logging.getLogger(__name__)


class BucketingAPIClient:
    def __init__(self, sdk_key: str, options: DVCCloudOptions):
        self.sdk_key = sdk_key
        self.options = options
        self.session = requests.Session()
        self.session.headers = {
            "Authorization": sdk_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.session.max_redirects = 0

    def _url(self, *path_args: str) -> str:
        return join(self.options.bucketing_API_URI, "v1", *path_args)

    def request(self, method: str, url: str, **kwargs) -> dict:
        retries_remaining = self.options.request_retries
        timeout = self.options.request_timeout

        attempts = 1
        while retries_remaining > 0:
            request_error: Optional[Exception] = None
            try:
                res: requests.Response = self.session.request(
                    method, url, timeout=timeout, **kwargs
                )
            except requests.exceptions.RequestException as e:
                request_error = e

            if res.status_code == 404:
                # Not a retryable error
                raise NotFoundException(url)
            elif 400 <= res.status_code < 500:
                # Not a retryable error
                raise CloudClientException(f"Bad request: HTTP {res.status_code}")

            if res.status_code >= 500:
                # Retryable error
                request_error = CloudClientException(
                    f"Server error: HTTP {res.status_code}"
                )

            if not request_error:
                break

            logger.error(
                f"DevCycle cloud bucketing request failed (attempt {attempts}): {request_error}"
            )
            retries_remaining -= 1
            if retries_remaining:
                retry_delay = exponential_backoff(attempts)
                time.sleep(retry_delay)
                attempts += 1
                continue

            raise CloudClientException(message="Retries exceeded", cause=request_error)

        data: dict = res.json()
        return data

    def variable(self, key: str, user: UserData) -> Variable:
        data = self.request("POST", self._url("variables", key), json=user.to_json())

        return Variable(
            _id=str(data.get("_id")),
            key=str(data.get("key")),
            type=str(data.get("type")),
            value=data.get("value"),
        )

    def variables(self, user: UserData) -> Dict[str, Variable]:
        data = self.request("POST", self._url("variables"), json=user.to_json())

        result: Dict[str, Variable] = {}
        for key, value in data.items():
            result[key] = Variable(
                _id=str(value.get("_id")),
                key=str(value.get("key")),
                type=str(value.get("type")),
                value=value.get("value"),
            )

        return result

    def features(self, user: UserData) -> Dict[str, Feature]:
        data = self.request("POST", self._url("features"), json=user.to_json())

        result: Dict[str, Feature] = {}
        for key, value in data.items():
            result[key] = Feature(
                _id=value.get("_id"),
                key=value.get("key"),
                type=value.get("type"),
                _variation=value.get("_variation"),
                variationKey=value.get("variationKey"),
                variationName=value.get("variationName"),
                evalReason=value.get("evalReason"),
            )

        return result

    def track(self, user: UserData, events: List[Event]) -> str:
        data = self.request(
            "POST",
            self._url("track"),
            json={
                "user": user.to_json(),
                "events": [event.to_json() for event in events],
            },
        )
        message = data.get("message", "")
        return message


def exponential_backoff(attempt: int) -> float:
    """
    Exponential backoff starting with 200ms +- 0...40ms jitter
    """
    delay = math.pow(2, attempt) * 0.1
    random_sum = delay * 0.2 * random.random()
    return delay + random_sum
