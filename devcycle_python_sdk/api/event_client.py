import json
import logging
import time
from os.path import join
from typing import Optional, List

import requests

from devcycle_python_sdk.api.backoff import exponential_backoff
from devcycle_python_sdk.options import DevCycleLocalOptions
from devcycle_python_sdk.exceptions import (
    APIClientError,
    NotFoundError,
    APIClientUnauthorizedError,
)
from devcycle_python_sdk.models.event import UserEventsBatchRecord

logger = logging.getLogger(__name__)


class EventAPIClient:
    def __init__(self, sdk_key: str, options: DevCycleLocalOptions):
        self.options = options
        self.session = requests.Session()
        self.session.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": sdk_key,
        }
        self.session.max_redirects = 0
        self.max_batch_retries = 0  # we don't retry events batches
        self.batch_url = join(self.options.events_api_uri, "v1/events/batch")

    def publish_events(self, batch: List[UserEventsBatchRecord]) -> str:
        """
        Attempts to send a batch of events to the server
        """
        retries_remaining = self.max_batch_retries + 1
        timeout = self.options.event_request_timeout_ms

        payload_json = json.dumps(
            {
                "batch": [record.to_json() for record in batch],
            }
        )

        attempts = 1
        while retries_remaining > 0:
            request_error: Optional[Exception] = None
            try:
                res: requests.Response = self.session.request(
                    "POST",
                    self.batch_url,
                    params={},
                    timeout=timeout,
                    data=payload_json,
                )
                if res.status_code == 401 or res.status_code == 403:
                    # Not a retryable error
                    raise APIClientUnauthorizedError("Invalid SDK Key")
                elif res.status_code == 404:
                    # Not a retryable error - bad URL
                    raise NotFoundError(self.batch_url)
                elif 400 <= res.status_code < 500:
                    # Not a retryable error
                    raise APIClientError(
                        f"Bad request: HTTP {res.status_code} - {res.text}"
                    )
                elif res.status_code >= 500:
                    # Retryable error
                    request_error = APIClientError(
                        f"Server error: HTTP {res.status_code}"
                    )
            except requests.exceptions.RequestException as e:
                request_error = e

            if not request_error:
                break

            logger.debug(
                f"DevCycle event batch request failed (attempt {attempts}): {request_error}"
            )
            retries_remaining -= 1
            if retries_remaining:
                retry_delay = exponential_backoff(
                    attempts, self.options.event_retry_delay_ms / 1000.0
                )
                time.sleep(retry_delay)
                attempts += 1
                continue

            raise APIClientError(message="Retries exceeded", cause=request_error)

        data: dict = res.json()
        return data.get("message", None)
