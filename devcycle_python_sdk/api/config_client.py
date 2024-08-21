import logging
import time
from http import HTTPStatus
from typing import Optional, Tuple
import email.utils
import requests

from devcycle_python_sdk.api.backoff import exponential_backoff
from devcycle_python_sdk.options import DevCycleLocalOptions
from devcycle_python_sdk.exceptions import (
    APIClientError,
    NotFoundError,
    APIClientUnauthorizedError,
)
from devcycle_python_sdk.util.strings import slash_join

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
        self.config_file_url = (
            slash_join(
                self.options.config_cdn_uri, "config", "v2", "server", self.sdk_key
            )
            + ".json"
        )

    def get_config(
        self, config_etag: Optional[str] = None, last_modified: Optional[str] = None
    ) -> Tuple[Optional[dict], Optional[str], Optional[str]]:
        """
        Get the config from the server. If the config_etag is provided, the server will only return the config if it
        has changed since the last request. If the config hasn't changed, the server will return a 304 Not Modified
        response.

        :param config_etag: The etag of the last config request
        :param last_modified: Last modified RFC1123 Timestamp of the stored config
        :return: A tuple containing the config and the etag of the config. If the config hasn't changed since the last
        request, the config will be None and the etag will be the same as the last request.
        """
        retries_remaining = self.max_config_retries
        timeout = self.options.config_request_timeout_ms / 1000.0

        url = self.config_file_url

        headers = {}
        if config_etag:
            headers["If-None-Match"] = config_etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        attempts = 1
        while retries_remaining > 0:
            request_error: Optional[Exception] = None
            try:
                res: requests.Response = self.session.request(
                    "GET", url, params={}, timeout=timeout, headers=headers
                )

                if (
                    res.status_code == HTTPStatus.UNAUTHORIZED
                    or res.status_code == HTTPStatus.FORBIDDEN
                ):
                    # Not a retryable error
                    raise APIClientUnauthorizedError("Invalid SDK Key")
                elif res.status_code == HTTPStatus.NOT_MODIFIED:
                    # the config hasn't changed since the last request
                    # don't return anything
                    return None, config_etag, last_modified
                elif res.status_code == HTTPStatus.NOT_FOUND:
                    # Not a retryable error
                    raise NotFoundError(url)
                elif (
                    HTTPStatus.BAD_REQUEST
                    <= res.status_code
                    < HTTPStatus.INTERNAL_SERVER_ERROR
                ):
                    # Not a retryable error
                    raise APIClientError(f"Bad request: HTTP {res.status_code}")
                elif res.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
                    # Retryable error
                    request_error = APIClientError(
                        f"Server error: HTTP {res.status_code}"
                    )
                else:
                    pass
            except requests.exceptions.RequestException as e:
                request_error = e

            if not request_error:
                break

            logger.debug(
                f"DevCycle config CDN request failed (attempt {attempts}): {request_error}"
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
        new_lastmodified = res.headers.get("Last-Modified", None)

        if last_modified and new_lastmodified:
            stored_lm = email.utils.parsedate_to_datetime(last_modified)
            response_lm = email.utils.parsedate_to_datetime(new_lastmodified)
            if stored_lm > response_lm:
                logger.warning(
                    "Request returned a last modified header older than the current stored timestamp. not saving config"
                )
                return None, None, None

        data: dict = res.json()
        return data, new_etag, new_lastmodified
