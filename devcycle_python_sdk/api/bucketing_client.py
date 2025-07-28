import logging
import time
from typing import Dict, List, Optional

import requests

from devcycle_python_sdk.api.backoff import exponential_backoff
from devcycle_python_sdk.options import DevCycleCloudOptions
from devcycle_python_sdk.exceptions import (
    CloudClientError,
    NotFoundError,
    CloudClientUnauthorizedError,
)
from devcycle_python_sdk.models.event import DevCycleEvent
from devcycle_python_sdk.models.feature import Feature
from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.variable import Variable
from devcycle_python_sdk.models.eval_reason import EvalReason
from devcycle_python_sdk.util.strings import slash_join

logger = logging.getLogger(__name__)


class BucketingAPIClient:
    def __init__(self, sdk_key: str, options: DevCycleCloudOptions):
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
        return slash_join(self.options.bucketing_api_uri, "v1", *path_args)

    def request(self, method: str, url: str, **kwargs) -> dict:
        retries_remaining = self.options.request_retries + 1
        timeout = self.options.request_timeout

        query_params = {}
        if self.options.enable_edge_db:
            query_params["enableEdgeDB"] = "true"

        attempts = 1
        while retries_remaining > 0:
            request_error: Optional[Exception] = None
            try:
                res: requests.Response = self.session.request(
                    method, url, params=query_params, timeout=timeout, **kwargs
                )

                if res.status_code == 401:
                    # Not a retryable error
                    raise CloudClientUnauthorizedError("Invalid SDK Key")
                elif res.status_code == 404:
                    # Not a retryable error
                    raise NotFoundError(url)
                elif 400 <= res.status_code < 500:
                    # Not a retryable error
                    raise CloudClientError(f"Bad request: HTTP {res.status_code}")
                elif res.status_code >= 500:
                    # Retryable error
                    request_error = CloudClientError(
                        f"Server error: HTTP {res.status_code}"
                    )
            except requests.exceptions.RequestException as e:
                request_error = e

            if not request_error:
                break

            logger.debug(
                f"DevCycle cloud bucketing request failed (attempt {attempts}): {request_error}"
            )
            retries_remaining -= 1
            if retries_remaining:
                retry_delay = exponential_backoff(
                    attempts, self.options.retry_delay / 1000.0
                )
                time.sleep(retry_delay)
                attempts += 1
                continue

            raise CloudClientError(message="Retries exceeded", cause=request_error)

        data: dict = res.json()
        return data

    def variable(self, key: str, user: DevCycleUser) -> Variable:
        data = self.request("POST", self._url("variables", key), json=user.to_json())

        eval_data = data.get("eval")
        eval_reason = None
        if eval_data is not None and isinstance(eval_data, dict):
            eval_reason = EvalReason.from_json(eval_data)

        return Variable(
            _id=data.get("_id"),
            key=data.get("key", ""),
            type=data.get("type", ""),
            value=data.get("value"),
            eval=eval_reason,
        )

    def variables(self, user: DevCycleUser) -> Dict[str, Variable]:
        data = self.request("POST", self._url("variables"), json=user.to_json())

        result: Dict[str, Variable] = {}
        for key, value in data.items():
            result[key] = Variable(
                _id=str(value.get("_id")),
                key=str(value.get("key")),
                type=str(value.get("type")),
                value=value.get("value"),
                isDefaulted=None,
                eval=(
                    EvalReason.from_json(value.get("eval"))
                    if value.get("eval")
                    else None
                ),
            )

        return result

    def features(self, user: DevCycleUser) -> Dict[str, Feature]:
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

    def track(self, user: DevCycleUser, events: List[DevCycleEvent]) -> str:
        data = self.request(
            "POST",
            self._url("track"),
            json={
                "user": user.to_json(),
                "events": [
                    event.to_json(use_bucketing_api_format=True) for event in events
                ],
            },
        )
        message = data.get("message", "")
        return message
