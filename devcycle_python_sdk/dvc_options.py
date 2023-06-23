import logging

logger = logging.getLogger(__name__)


class DevCycleCloudOptions:
    def __init__(
        self,
        enable_edge_db: bool = False,
        events_api_uri: str = "https://events.devcycle.com/",
        config_cdn_uri: str = "https://config-cdn.devcycle.com/",
        bucketing_api_uri: str = "https://bucketing-api.devcycle.com/",
        request_timeout: int = 5,  # seconds
        request_retries: int = 5,
        retry_delay: int = 200,  # milliseconds
    ):
        self.enable_edge_db = enable_edge_db
        self.events_API_URI = events_api_uri
        self.config_CDN_URI = config_cdn_uri
        self.bucketing_API_URI = bucketing_api_uri
        self.request_timeout = request_timeout
        self.request_retries = request_retries
        self.retry_delay = retry_delay


class DevCycleLocalOptions:
    def __init__(
        self,
        config_cdn_uri: str = "https://config-cdn.devcycle.com/",
        config_request_timeout_ms: int = 5000,
        config_polling_interval_ms: int = 1000,
        config_retry_delay_ms: int = 200,  # milliseconds
        on_client_initialized: callable = None,
        events_api_uri: str = "https://events.devcycle.com/",
        max_event_queue_size: int = 2000,
        event_flush_interval_ms: int = 10000,
        flush_event_queue_size: int = 1000,
        event_request_chunk_size: int = 100,
        disable_automatic_event_logging: bool = False,
        disable_custom_event_logging: bool = False,
    ):
        self.events_API_URI = events_api_uri
        self.config_CDN_URI = config_cdn_uri
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

        if self.flush_event_queue_size >= self.max_event_queue_size:
            logger.warning(
                "flushEventQueueSize: %d must be smaller than maxEventQueueSize: %d",
                self.flush_event_queue_size,
                self.max_event_queue_size,
            )
            self.flush_event_queue_size = self.max_event_queue_size - 1

        if self.event_request_chunk_size > self.flush_event_queue_size:
            logger.warning(
                "eventRequestChunkSize: %d must be smaller than flushEventQueueSize: %d",
                self.event_request_chunk_size,
                self.flush_event_queue_size,
            )
            self.event_request_chunk_size = 100

        if self.event_request_chunk_size > self.max_event_queue_size:
            logger.warning(
                "eventRequestChunkSize: %d must be smaller than maxEventQueueSize: %d",
                self.event_request_chunk_size,
                self.max_event_queue_size,
            )
            self.event_request_chunk_size = 100

        if self.flush_event_queue_size > 20000:
            logger.warning(
                "flushEventQueueSize: %d must be smaller than 20,000",
                self.flush_event_queue_size,
            )
            self.flush_event_queue_size = 20000

        if self.max_event_queue_size > 20000:
            logger.warning(
                "maxEventQueueSize: %d must be smaller than 20,000",
                self.max_event_queue_size,
            )
            self.max_event_queue_size = 20000
