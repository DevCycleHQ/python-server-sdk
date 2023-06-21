import logging
import math
import random
import time
import requests

from os.path import join
from typing import Optional, Tuple
from http import HTTPStatus

from devcycle_python_sdk.dvc_options import DevCycleLocalOptions
from devcycle_python_sdk.exceptions import (
    APIClientError,
    NotFoundError,
    APIClientUnauthorizedError,
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

    def get_config(self, config_etag: Optional[str] = None) -> Tuple[Optional[dict], Optional[str]]:
        """
        Get the config from the server. If the config_etag is provided, the server will only return the config if it
        has changed since the last request. If the config hasn't changed, the server will return a 304 Not Modified
        response.

        :param config_etag: The etag of the last config request

        :return: A tuple containing the config and the etag of the config. If the config hasn't changed since the last
        request, the config will be None and the etag will be the same as the last request.
        """
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

                if res.status_code == HTTPStatus.UNAUTHORIZED or res.status_code == HTTPStatus.FORBIDDEN:
                    # Not a retryable error
                    raise APIClientUnauthorizedError("Invalid SDK Key")
                elif res.status_code == HTTPStatus.NOT_MODIFIED:
                    # the config hasn't changed since the last request
                    # don't return anything
                    return None, config_etag
                elif res.status_code == HTTPStatus.NOT_FOUND:
                    # Not a retryable error
                    raise NotFoundError(url)
                elif HTTPStatus.BAD_REQUEST <= res.status_code < HTTPStatus.INTERNAL_SERVER_ERROR:
                    # Not a retryable error
                    raise APIClientError(f"Bad request: HTTP {res.status_code}")
                elif res.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
                    # Retryable error
                    request_error = APIClientError(
                        f"Server error: HTTP {res.status_code}"
                    )
            except requests.exceptions.RequestException as e:
                request_error = e

            if not request_error:
                break

            logger.warning(
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

            raise APIClientError(message="Retries exceeded", cause=request_error)

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
