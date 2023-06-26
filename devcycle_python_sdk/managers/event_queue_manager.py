import threading
import time
import logging
import json
from typing import Optional

from devcycle_python_sdk.dvc_options import DevCycleLocalOptions
from devcycle_python_sdk.api.local_bucketing import LocalBucketing
from devcycle_python_sdk.api.config_client import ConfigAPIClient
from devcycle_python_sdk.exceptions import (
    APIClientError,
    APIClientUnauthorizedError,
)

logger = logging.getLogger(__name__)


class EventQueueManager(threading.Thread):
    def __init__(
            self,
            sdk_key: str,
            options: DevCycleLocalOptions,
            local_bucketing: LocalBucketing,
    ):
        if sdk_key is None or sdk_key == "":
            raise ValueError("DevCycle is not yet initialized to publish events.")

        self._sdk_key = sdk_key

        self._options = options
        self.local_bucketing = local_bucketing

        # TODO setup proper options for the event queue
        event_options: dict = {}
        event_options_json = json.dumps(event_options)
        self.local_bucketing.init_event_queue(event_options_json)

        self._event_api_client = ConfigAPIClient(self._sdk_key, self._options)

        self._processing_enabled = True
        self.flush_lock = threading.Lock()
        self.daemon = True
        self.start()

    def _flush_events(self):
        if self.flush_lock.locked():
            return

        with self.flush_lock:
            try:
                payloads = self.local_bucketing.flush_event_queue()
            except Exception as e:
                logger.error(f"Error flushing event payloads: {str(e)}")

            if payloads:
                logger.info(f"Flushing {len(payloads)} event payloads")
                event_count = 0
                for payload in payloads:
                    event_count += payload.eventCount
                    self._publishEventPayload(payload)
                logger.info(f"DVC Flush {event_count} events, for {len(payloads)} users")

    def _publishEventPayload(self, payload) -> None:
        try:
            self._event_api_client.publish_event_payload(payload)
            self.local_bucketing.on_payload_success(payload.payloadId)
        except APIClientError as e:
            allow_retry = True
            if isinstance(e, APIClientUnauthorizedError):
                logger.error("Unauthorized to publish events, please check your SDK key")
                self._processing_enabled = False
                allow_retry = False

            self.local_bucketing.on_payload_failure(payload.payloadId, allow_retry)

    def run(self):
        while self._processing_enabled:
            try:
                self._flush_events()
            except Exception as e:
                logger.info(f"DVC Error flushing events: {str(e)}")
            time.sleep(self._options.event_flush_interval_ms / 1000.0)

    def close(self):
        self._processing_enabled = False
        self.join(timeout=5.0)
