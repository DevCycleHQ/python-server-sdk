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
    CloudClientUnauthorizedError,
    CloudClientError,
)
from wsgiref.handlers import format_date_time
from devcycle_python_sdk.options import DevCycleLocalOptions
from devcycle_python_sdk.managers.sse_manager import SSEManager

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

        self._config_api_client = ConfigAPIClient(self._sdk_key, self._options)

        self._polling_enabled = True
        self.daemon = True
        self.start()

    def is_initialized(self) -> bool:
        return self._config is not None

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
                if self._sse_manager is None:
                    self._sse_manager = SSEManager(
                        self.sse_state,
                        self.sse_error,
                        self.sse_message,
                    )
                self._sse_manager.update(self._config)

            if (
                trigger_on_client_initialized
                and self._options.on_client_initialized is not None
            ):
                try:
                    self._options.on_client_initialized()
                except Exception as e:
                    # consume any error
                    logger.warning(
                        f"DevCycle: Error received from on_client_initialized callback: {str(e)}"
                    )
        except CloudClientError as e:
            logger.warning(f"DevCycle: Config fetch failed. Status: {str(e)}")
        except CloudClientUnauthorizedError:
            logger.error(
                "DevCycle: Unauthorized to get config. Aborting config polling."
            )
            self._polling_enabled = False

    def run(self):
        while self._polling_enabled:
            try:
                self._get_config()
            except Exception as e:
                if self._polling_enabled:
                    # Only log a warning if we're still polling
                    logger.warning(
                        f"DevCycle: Error polling for config changes: {str(e)}"
                    )
            if self._sse_connected:
                time.sleep(self._sse_polling_interval / 1000.0)
            else:
                time.sleep(self._options.config_polling_interval_ms / 1000.0)

    def sse_message(self, message: ld_eventsource.actions.Event):
        if self._sse_connected is False:
            self._sse_connected = True
            logger.info("DevCycle: Connected to SSE stream")
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
        logger.debug(f"DevCycle: Received SSE error: {error}")

    def sse_state(self, state: ld_eventsource.actions.Start):
        self._sse_connected = True
        logger.info("DevCycle: Connected to SSE stream")

    def close(self):
        self._polling_enabled = False
