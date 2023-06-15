import logging
import math
import random
import time
from os.path import join
from typing import Optional

import requests

from devcycle_python_sdk.dvc_options import DevCycleLocalOptions
from devcycle_python_sdk.exceptions import (
    CloudClientError,
    NotFoundError,
    CloudClientUnauthorizedError,
)

logger = logging.getLogger(__name__)


class ConfigAPIClient:
    def __init__(self, sdk_key: str, options: DevCycleLocalOptions):
        self.sdk_key = sdk_key
        self.options = options
        self.session = requests.Session()
        self.session.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.session.max_redirects = 0
        self.max_config_retries = 2

    def _config_file_url(self) -> str:
        return join(self.options.config_CDN_URI, "v1", "server", self.sdk_key, ".json")

    def get_config(self, config_etag: str = None) -> (dict, str):
        retries_remaining = self.max_config_retries
        timeout = self.options.config_request_timeout_ms / 1000.0

        url = self._config_file_url()

        headers = {}
        if config_etag:
            headers["If-None-Match"] = config_etag

        attempts = 1
        while retries_remaining > 0:
            request_error: Optional[Exception] = None
            try:
                res: requests.Response = self.session.request(
                    "GET", url, params={}, timeout=timeout, headers=headers
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

            logger.error(
                f"DevCycle cloud bucketing request failed (attempt {attempts}): {request_error}"
            )
            retries_remaining -= 1
            if retries_remaining:
                retry_delay = exponential_backoff(
                    attempts, self.options.config_retry_delay_ms / 1000.0
                )
                time.sleep(retry_delay)
                attempts += 1
                continue

            raise CloudClientError(message="Retries exceeded", cause=request_error)

        new_etag = res.headers.get("ETag", None)

        data: dict = res.json()
        return data, new_etag


def exponential_backoff(attempt: int, base_delay: float) -> float:
    """
    Exponential backoff starting with 200ms +- 0...40ms jitter
    """
    delay = math.pow(2, attempt) * base_delay / 2.0
    random_sum = delay * 0.1 * random.random()
    return delay + random_sum
