import threading
import time
import logging
import json

from devcycle_python_sdk.dvc_options import DevCycleLocalOptions
from devcycle_python_sdk.api.local_bucketing import LocalBucketing
from devcycle_python_sdk.api.event_client import EventAPIClient
from devcycle_python_sdk.exceptions import (
    APIClientError,
    APIClientUnauthorizedError,
)
from devcycle_python_sdk.models.event import FlushPayload, EventType


logger = logging.getLogger(__name__)


class EventQueueManager(threading.Thread):
    def __init__(
        self,
        sdk_key: str,
        options: DevCycleLocalOptions,
        local_bucketing: LocalBucketing,
    ):
        super().__init__()

        if sdk_key is None or sdk_key == "":
            raise ValueError("DevCycle is not yet initialized to publish events.")

        self._sdk_key = sdk_key
        self._options = options
        self._local_bucketing = local_bucketing
        self._event_api_client = EventAPIClient(self._sdk_key, self._options)
        self.flush_lock = threading.Lock()

        # Setup the event queue inside the WASM module
        event_options_json = json.dumps(self._options.event_queue_options())
        self._local_bucketing.init_event_queue(event_options_json)

        # Only start event processing thread if event logging is enabled
        if not (
            self._options.disable_custom_event_logging
            and self._options.disable_automatic_event_logging
        ):
            self._processing_enabled = True
            self.daemon = True
            self.start()
        else:
            self._processing_enabled = False

    def _flush_events(self):
        if self.flush_lock.locked():
            return

        with self.flush_lock:
            try:
                payloads = self._local_bucketing.flush_event_queue()
            except Exception as e:
                logger.error(f"Error flushing event payloads: {str(e)}")

            if payloads:
                logger.info(f"DVC Flush {len(payloads)} event payloads")
                event_count = 0
                for payload in payloads:
                    event_count += payload.eventCount
                    self._publish_event_payload(payload)
                logger.info(
                    f"DVC Flush {event_count} events, for {len(payloads)} users"
                )

    def _publish_event_payload(self, payload: FlushPayload) -> None:
        if payload and payload.records:
            try:
                self._event_api_client.publish_events(payload.records)
                self._local_bucketing.on_event_payload_success(payload.payloadId)
            except APIClientError as e:
                allow_retry = True
                if isinstance(e, APIClientUnauthorizedError):
                    logger.error(
                        "Unauthorized to publish events, please check your SDK key"
                    )
                    self._processing_enabled = False
                    allow_retry = False

                self._local_bucketing.on_event_payload_failure(
                    payload.payloadId, allow_retry
                )

    def is_event_logging_disabled(self, event_type: str) -> bool:
        if event_type in [
            EventType.VariableDefaulted,
            EventType.VariableEvaluated,
            EventType.AggVariableDefaulted,
            EventType.AggVariableEvaluated,
        ]:
            return self._options.disable_automatic_event_logging
        else:
            return self._options.disable_custom_event_logging

    def run(self):
        while self._processing_enabled:
            try:
                self._flush_events()
            except Exception as e:
                logger.info(f"DVC Error flushing events: {str(e)}")
            time.sleep(self._options.event_flush_interval_ms / 1000.0)

    def close(self):
        self._processing_enabled = False
        self.join(timeout=1)
