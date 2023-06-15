import threading
import time
import logging

logger = logging.getLogger(__name__)


class ConfigManager(threading.Thread):
    def __init__(self):
        super(ConfigManager, self).__init__()

        self.config: str = None
        self.config_etag: str = ""

        self.polling_enabled = True
        self.start()

    def get_config(self):
        print("Getting config from server")
        # newConfig = apiClient.loadConfig()
        # if config is None:
        # do initialized callback
        # config = newConfig

    def run(self):
        while self.polling_enabled:
            print("Polling for config changes")
            try:
                self.get_config()
            except Exception as e:
                logger.info(f"Error polling for config changes: {str(e)}")
            time.sleep(5)

    def close(self):
        self.polling_enabled = False
        self.stop()
        self.join(timeout=10.0)
