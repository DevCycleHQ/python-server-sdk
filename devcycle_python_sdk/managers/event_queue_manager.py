import threading
import logging
import json
import time
from typing import Optional

from devcycle_python_sdk.dvc_options import DevCycleLocalOptions
from devcycle_python_sdk.api.local_bucketing import LocalBucketing
from devcycle_python_sdk.api.event_client import EventAPIClient
from devcycle_python_sdk.exceptions import (
    APIClientError,
    APIClientUnauthorizedError,
    NotFoundError,
)
from devcycle_python_sdk.models.event import (
    FlushPayload,
    Event,
    EventType,
)
from devcycle_python_sdk.models.user import User
from devcycle_python_sdk.models.bucketed_config import BucketedConfig


logger = logging.getLogger(__name__)


class QueueFullError(Exception):
    pass


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
        self._flush_lock = threading.Lock()

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

    def _flush_events(self) -> int:
        if self._flush_lock.locked():
            return 0

        with self._flush_lock:
            try:
                payloads = self._local_bucketing.flush_event_queue()
            except Exception as e:
                logger.error(f"Error flushing event payloads: {str(e)}")

            event_count = 0
            if payloads:
                logger.info(f"DVC Flush {len(payloads)} event payloads")
                for payload in payloads:
                    event_count += payload.eventCount
                    self._publish_event_payload(payload)
                logger.info(
                    f"DVC Flush {event_count} events, for {len(payloads)} users"
                )
            return event_count

    def _publish_event_payload(self, payload: FlushPayload) -> None:
        if payload and payload.records:
            try:
                self._event_api_client.publish_events(payload.records)
                self._local_bucketing.on_event_payload_success(payload.payloadId)
            except (APIClientUnauthorizedError, NotFoundError):
                logger.error(
                    "Unauthorized to publish events, please check your SDK key"
                )
                # stop the thread
                self._processing_enabled = False
                self._local_bucketing.on_event_payload_failure(payload.payloadId, False)
            except NotFoundError as e:
                logger.error(
                    f"Unable to reach the DevCycle Events API service: {str(e)}"
                )
                self._processing_enabled = False
                self._local_bucketing.on_event_payload_failure(payload.payloadId, False)
            except APIClientError as e:
                logger.warning(f"Error publishing events: {str(e)}")
                self._local_bucketing.on_event_payload_failure(payload.payloadId, True)

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
        try:
            self._flush_events()
        except Exception as e:
            logger.info(f"DVC Error flushing events when closing client: {str(e)}")
        self.join(timeout=1)

    def queue_event(self, user: User, event: Event) -> None:
        if user is None:
            raise ValueError("user cannot be None")

        if event is None:
            raise ValueError("event cannot be None")

        if not event.type:
            raise ValueError("event type not set")

        try:
            self._check_queue_status()
        except QueueFullError:
            logger.warning(f"Event queue is full, dropping event: {event}")
            return

        user_json = json.dumps(user.to_json())
        event_json = json.dumps(event.to_json())
        self._local_bucketing.queue_event(user_json, event_json)

    def queue_aggregate_event(
        self, event: Event, bucketed_config: Optional[BucketedConfig]
    ) -> None:
        if event is None:
            raise ValueError("event cannot be None")

        if not event.type:
            raise ValueError("event type not set")

        if not event.target:
            raise ValueError("event target not set")

        try:
            self._check_queue_status()
        except QueueFullError:
            logger.warning("Event queue is full, dropping event")
            return

        event_json = json.dumps(event.to_json())
        if bucketed_config and bucketed_config.variable_variation_map:
            variation_map_json = json.dumps(bucketed_config.variable_variation_map)
        else:
            variation_map_json = "{}"
        self._local_bucketing.queue_aggregate_event(event_json, variation_map_json)

    def _check_queue_status(self) -> None:
        if self._flush_needed() and not self._flush_lock.locked():
            self._flush_events()

        if self._queue_full():
            raise QueueFullError()

    def _flush_needed(self) -> bool:
        queue_size = self._local_bucketing.get_event_queue_size()
        return queue_size >= self._options.flush_event_queue_size

    def _queue_full(self) -> bool:
        queue_size = self._local_bucketing.get_event_queue_size()
        return queue_size >= self._options.max_event_queue_size
