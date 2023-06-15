import threading
import time
import logging

from devcycle_python_sdk.dvc_options import DevCycleLocalOptions
from devcycle_python_sdk.api.local_bucketing import LocalBucketing
from devcycle_python_sdk.api.config_client import ConfigAPIClient
from devcycle_python_sdk.exceptions import CloudClientUnauthorizedError, CloudClientError

logger = logging.getLogger(__name__)


class EnvironmentConfigManager(threading.Thread):
    def __init__(self, sdk_key: str, options: DevCycleLocalOptions, local_bucketing: LocalBucketing):
        super().__init__()

        self._sdk_key = sdk_key
        self._options = options
        self._local_bucketing = local_bucketing

        self._config: dict = None
        self._config_etag: str = None

        self._config_api_client = ConfigAPIClient(self._sdk_key, self._options)

        self._polling_enabled = True
        self.daemon = True
        self.start()

    def is_initialized(self) -> bool:
        return self._config is not None

    def get_config(self):
        try:
            new_config, new_etag = self._config_api_client.get_config(config_etag=self._config_etag)

            if new_config is None and new_etag == self._config_etag:
                # no change to the config since last request
                return

            trigger_on_client_initialized = self._config is None
            self._config = new_config
            self._config_etag = new_etag
            self._local_bucketing.store_config(self._sdk_key, self._config)

            if trigger_on_client_initialized and self._options.on_client_initialized is not None:
                try:
                    self._options.on_client_initialized()
                except Exception as e:
                    # consume any error
                    logger.warning(f"Error in on_client_initialized callback: {str(e)}")
        except CloudClientError as e:
            logger.warning(f"Config fetch failed. Status: {str(e)}")
        except CloudClientUnauthorizedError:
            logger.error("Unauthorized to get config. Aborting config polling.")
            self._polling_enabled = False

    def run(self):
        while self._polling_enabled:
            try:
                self.get_config()
            except Exception as e:
                logger.info(f"Error polling for config changes: {str(e)}")
            time.sleep(self._options.config_polling_interval_ms / 1000.0)

    def close(self):
        self._polling_enabled = False
        self.join(timeout=5.0)
