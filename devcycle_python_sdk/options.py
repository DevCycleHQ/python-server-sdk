import logging
from typing import Callable, Optional, Dict, Any, List

from devcycle_python_sdk.models.eval_hook import EvalHook

logger = logging.getLogger(__name__)


class DevCycleCloudOptions:
    """
    Options for configuring the DevCycle Cloud SDK.
    """

    def __init__(
        self,
        enable_edge_db: bool = False,
        bucketing_api_uri: str = "https://bucketing-api.devcycle.com/",
        request_timeout: int = 5,  # seconds
        request_retries: int = 5,
        retry_delay: int = 200,  # milliseconds
        eval_hooks: Optional[List[EvalHook]] = None,
    ):
        self.enable_edge_db = enable_edge_db
        self.bucketing_api_uri = bucketing_api_uri
        self.request_timeout = request_timeout
        self.request_retries = request_retries
        self.retry_delay = retry_delay
        self.eval_hooks = eval_hooks if eval_hooks is not None else []


class DevCycleLocalOptions:
    """
    Options for configuring the DevCycle Local Bucketing SDK.
    """

    def __init__(
        self,
        config_cdn_uri: str = "https://config-cdn.devcycle.com/",
        config_request_timeout_ms: int = 5000,
        config_polling_interval_ms: int = 1000,
        config_retry_delay_ms: int = 200,  # milliseconds
        on_client_initialized: Optional[Callable] = None,
        events_api_uri: str = "https://events.devcycle.com/",
        max_event_queue_size: int = 2000,
        event_flush_interval_ms: int = 10000,
        flush_event_queue_size: int = 1000,
        event_request_chunk_size: int = 100,
        event_request_timeout_ms: int = 10000,
        event_retry_delay_ms: int = 200,  # milliseconds
        disable_automatic_event_logging: bool = False,
        disable_custom_event_logging: bool = False,
        enable_beta_realtime_updates: bool = False,
        disable_realtime_updates: bool = False,
        eval_hooks: Optional[List[EvalHook]] = None,
    ):
        self.events_api_uri = events_api_uri
        self.config_cdn_uri = config_cdn_uri
        self.config_request_timeout_ms = config_request_timeout_ms
        self.config_polling_interval_ms = config_polling_interval_ms
        self.max_event_queue_size = max_event_queue_size
        self.event_flush_interval_ms = event_flush_interval_ms
        self.flush_event_queue_size = flush_event_queue_size
        self.event_request_chunk_size = event_request_chunk_size
        self.disable_automatic_event_logging = disable_automatic_event_logging
        self.disable_custom_event_logging = disable_custom_event_logging
        self.config_retry_delay_ms = config_retry_delay_ms
        self.on_client_initialized = on_client_initialized
        self.event_request_timeout_ms = event_request_timeout_ms
        self.event_retry_delay_ms = event_retry_delay_ms
        self.disable_realtime_updates = disable_realtime_updates

        if enable_beta_realtime_updates:
            logger.warning(
                "DevCycle: `enable_beta_realtime_updates` is deprecated and will be removed in a future release.",
            )

        self.eval_hooks = eval_hooks if eval_hooks is not None else []

        if self.flush_event_queue_size >= self.max_event_queue_size:
            logger.warning(
                f"DevCycle: flush_event_queue_size: {self.flush_event_queue_size} must be smaller than max_event_queue_size: {self.max_event_queue_size}"
            )
            self.flush_event_queue_size = self.max_event_queue_size - 1

        if self.event_request_chunk_size > self.flush_event_queue_size:
            logger.warning(
                f"DevCycle: event_request_chunk_size: {self.event_request_chunk_size} must be smaller than flush_event_queue_size: {self.flush_event_queue_size}"
            )
            self.event_request_chunk_size = 100

        if self.event_request_chunk_size > self.max_event_queue_size:
            logger.warning(
                f"DevCycle: event_request_chunk_size: {self.event_request_chunk_size} must be smaller than max_event_queue_size: { self.max_event_queue_size}"
            )
            self.event_request_chunk_size = 100

        if self.flush_event_queue_size > 20000:
            logger.warning(
                f"DevCycle: flush_event_queue_size: {self.flush_event_queue_size} must be smaller than 20,000"
            )
            self.flush_event_queue_size = 20000

        if self.max_event_queue_size > 20000:
            logger.warning(
                f"DevCycle: max_event_queue_size: {self.max_event_queue_size} must be smaller than 20,000"
            )
            self.max_event_queue_size = 20000

    def event_queue_options(self) -> Dict[str, Any]:
        """
        Returns a read-only view of the options that are relevant to the event subsystem
        """
        return {
            "flushEventsMS": self.event_flush_interval_ms,
            "disableAutomaticEventLogging": self.disable_automatic_event_logging,
            "disableCustomEventLogging": self.disable_custom_event_logging,
            "maxEventsPerFlush": self.max_event_queue_size,
            "minEventsPerFlush": self.flush_event_queue_size,
            "eventRequestChunkSize": self.event_request_chunk_size,
            "eventsAPIBasePath": self.events_api_uri,
        }
