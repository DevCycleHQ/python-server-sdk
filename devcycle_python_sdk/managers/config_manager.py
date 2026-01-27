import json
import logging
import threading
import time
from datetime import datetime
from typing import Optional

import ld_eventsource.actions

from devcycle_python_sdk.api.config_client import ConfigAPIClient
from devcycle_python_sdk.api.local_bucketing import LocalBucketing
from devcycle_python_sdk.exceptions import (
    APIClientError,
    APIClientUnauthorizedError,
)
from wsgiref.handlers import format_date_time
from devcycle_python_sdk.options import DevCycleLocalOptions
from devcycle_python_sdk.managers.sse_manager import SSEManager
from devcycle_python_sdk.models.config_metadata import ConfigMetadata

logger = logging.getLogger(__name__)


class EnvironmentConfigManager(threading.Thread):
    def __init__(
        self,
        sdk_key: str,
        options: DevCycleLocalOptions,
        local_bucketing: LocalBucketing,
    ):
        super().__init__()

        self._sdk_key = sdk_key
        self._options = options
        self._local_bucketing = local_bucketing
        self._sse_manager: Optional[SSEManager] = None
        self._sse_polling_interval = 1000 * 60 * 15 * 60
        self._sse_connected = False
        self._config: Optional[dict] = None
        self._config_etag: Optional[str] = None
        self._config_lastmodified: Optional[str] = None
        self._sse_reconnecting = False
        self._last_reconnect_attempt_time: Optional[float] = None
        self._sse_reconnect_lock = threading.Lock()

        self._config_api_client = ConfigAPIClient(self._sdk_key, self._options)

        self._polling_enabled = True
        self.daemon = True
        self.start()

    def is_initialized(self) -> bool:
        return self._config is not None

    def _recreate_sse_connection(self):
        """Recreate the SSE connection with the current config."""
        with self._sse_reconnect_lock:
            if self._config is None or self._options.disable_realtime_updates:
                logger.debug("Skipping SSE recreation - no config or updates disabled")
                return

            try:
                # Close existing connection if present
                if self._sse_manager is not None and self._sse_manager.client is not None:
                    logger.debug("Closing existing SSE connection before recreating")
                    self._sse_manager.client.close()
                    if self._sse_manager.read_thread.is_alive():
                        self._sse_manager.read_thread.join(timeout=1.0)

                # Create new SSE manager
                self._sse_manager = SSEManager(
                    self.sse_state,
                    self.sse_error,
                    self.sse_message,
                )
                self._sse_manager.update(self._config)
                logger.info("SSE connection recreated successfully")
            except Exception as e:
                logger.error(f"Devcycle: Failed to recreate SSE connection: {e}")

    def _delayed_sse_reconnect(self):
        """Delayed SSE reconnection to allow error state to settle."""
        try:
            logger.debug("Waiting 2 seconds before reconnecting SSE...")
            time.sleep(2.0)
            logger.debug("Attempting to recreate SSE connection")
            self._recreate_sse_connection()
        except Exception as e:
            logger.error(f"Devcycle: Error during delayed SSE reconnection: {e}")
        finally:
            # Always clear the reconnecting flag when done (success or failure)
            with self._sse_reconnect_lock:
                self._sse_reconnecting = False

    def _get_config(self, last_modified: Optional[float] = None):
        try:
            lm_header = self._config_lastmodified
            if last_modified is not None:
                lm_timestamp = datetime.fromtimestamp(last_modified)
                lm_header = format_date_time(time.mktime(lm_timestamp.timetuple()))

            new_config, new_etag, new_lastmodified = self._config_api_client.get_config(
                config_etag=self._config_etag, last_modified=lm_header
            )

            # Abort early if the last modified is before the sent one.
            if new_config is None and new_etag is None and new_lastmodified is None:
                return
            if new_config is None and new_etag == self._config_etag:
                # api not returning data and the etag is the same
                # no change to the config since last request
                return
            elif new_config is None:
                logger.warning(
                    "DevCycle: Config CDN fetch returned no data with a different etag"
                )
                return

            trigger_on_client_initialized = self._config is None

            self._config = new_config
            self._config_etag = new_etag
            self._config_lastmodified = new_lastmodified

            json_config = json.dumps(self._config)
            self._local_bucketing.store_config(json_config)
            if not self._options.disable_realtime_updates:
                if (
                    self._sse_manager is None
                    or self._sse_manager.client is None
                    or not self._sse_manager.read_thread.is_alive()
                ):
                    logger.info("DevCycle: SSE connection not active, creating new connection")
                    self._recreate_sse_connection()

            if (
                trigger_on_client_initialized
                and self._options.on_client_initialized is not None
            ):
                try:
                    self._options.on_client_initialized()
                except Exception as e:
                    logger.warning(
                        f"DevCycle: Error received from on_client_initialized callback: {str(e)}"
                    )
        except APIClientError as e:
            logger.warning(f"DevCycle: Config fetch failed. Status: {str(e)}")
        except APIClientUnauthorizedError:
            logger.error(
                "DevCycle: Error initializing DevCycle: Invalid SDK key provided."
            )
            self._polling_enabled = False

    def get_config_metadata(self) -> Optional[ConfigMetadata]:
        return self._local_bucketing.get_config_metadata()

    def run(self):
        while self._polling_enabled:
            try:
                self._get_config()
            except Exception as e:
                if self._polling_enabled:
                    logger.warning(
                        f"DevCycle: Error polling for config changes: {str(e)}"
                    )
            if self._sse_connected:
                time.sleep(self._sse_polling_interval / 1000.0)
            else:
                time.sleep(self._options.config_polling_interval_ms / 1000.0)

    def sse_message(self, message: ld_eventsource.actions.Event):
        # Received a message from the SSE stream but our sse_connected is False, so we need to set it to True
        if not self._sse_connected:
            self.sse_state(None)
        logger.info(f"DevCycle: Received message: {message.data}")
        sse_message = json.loads(message.data)
        dvc_data = json.loads(sse_message.get("data"))
        if (
            dvc_data.get("type") == "refetchConfig"
            or dvc_data.get("type") == ""
            or dvc_data.get("type") is None
        ):
            logger.info("DevCycle: Received refetchConfig message - updating config")
            self._get_config(dvc_data["lastModified"] / 1000.0)

    def sse_error(self, error: ld_eventsource.actions.Fault):
        self._sse_connected = False
        logger.debug(f"SSE connection error: {error.error}")

        current_time = time.time()
        min_reconnect_interval = 5.0

        with self._sse_reconnect_lock:
            # Check if we're already reconnecting
            if self._sse_reconnecting:
                logger.debug("Reconnection already in progress, skipping")
                return
            
            # Check if we need to wait for backoff
            if (self._last_reconnect_attempt_time is not None and
                current_time - self._last_reconnect_attempt_time < min_reconnect_interval):
                logger.debug(
                    f"Skipping reconnection, waiting for backoff period ({min_reconnect_interval}s)"
                )
                return
            
            # Mark that we're now reconnecting
            self._sse_reconnecting = True
            self._last_reconnect_attempt_time = current_time
        
        logger.info("Attempting SSE reconnection...")
        
        # Schedule reconnection in a separate thread
        reconnect_thread = threading.Thread(
            target=self._delayed_sse_reconnect,
            daemon=True
        )
        reconnect_thread.start()

    def sse_state(self, state: Optional[ld_eventsource.actions.Start]):
        if not self._sse_connected:
            self._sse_connected = True
            logger.info("DevCycle: Connected to SSE stream")
            
            # Clear reconnection state on successful connection
            with self._sse_reconnect_lock:
                self._sse_reconnecting = False
                self._last_reconnect_attempt_time = None
        else:
            logger.debug("SSE keepalive received")

    def close(self):
        self._polling_enabled = False
        if self._sse_manager is not None and self._sse_manager.client is not None:
            self._sse_manager.client.close()