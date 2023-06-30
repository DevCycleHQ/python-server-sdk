import logging
import json
import time
import uuid
import unittest
from unittest.mock import patch, MagicMock

from devcycle_python_sdk import DevCycleLocalOptions
from devcycle_python_sdk.managers.config_manager import EnvironmentConfigManager
from test.fixture.data import small_config_json

logger = logging.getLogger(__name__)


class EnvironmentConfigManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sdk_key = "dvc_server_" + str(uuid.uuid4())
        self.test_local_bucketing = MagicMock()
        self.test_options = DevCycleLocalOptions(config_polling_interval_ms=500)

        self.test_etag = str(uuid.uuid4())
        self.test_config_json = small_config_json()
        self.test_config_string = json.dumps(self.test_config_json)

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    def test_init(self, mock_get_config):
        mock_get_config.return_value = (self.test_config_json, self.test_etag)
        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )

        # sleep to allow polling thread to load the config
        time.sleep(0.1)
        mock_get_config.assert_called_once_with(config_etag=None)

        self.assertTrue(config_manager._polling_enabled)
        self.assertTrue(config_manager.is_alive())
        self.assertTrue(config_manager.daemon)
        self.assertEqual(config_manager._config_etag, self.test_etag)
        self.assertDictEqual(config_manager._config, self.test_config_json)
        self.test_local_bucketing.store_config.assert_called_once_with(
            self.test_config_string
        )
        self.assertTrue(config_manager.is_initialized())

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    def test_init_with_client_callback(self, mock_get_config):
        mock_get_config.return_value = (self.test_config_json, self.test_etag)

        mock_callback = MagicMock()

        self.test_options.on_client_initialized = mock_callback

        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)
        mock_get_config.assert_called_once_with(config_etag=None)
        self.assertEqual(config_manager._config_etag, self.test_etag)
        self.assertDictEqual(config_manager._config, self.test_config_json)
        self.test_local_bucketing.store_config.assert_called_once_with(
            self.test_config_string
        )
        self.assertTrue(config_manager.is_initialized())
        mock_callback.assert_called_once()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    def test_init_with_client_callback_with_error(self, mock_get_config):
        mock_get_config.return_value = (self.test_config_json, self.test_etag)
        mock_callback = MagicMock()
        mock_callback.side_effect = Exception(
            "Badly written callback generates an exception"
        )

        self.test_options.on_client_initialized = mock_callback

        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        # the callback error should not negatively impact initialization of the config manager
        time.sleep(0.1)
        mock_get_config.assert_called_once_with(config_etag=None)
        self.assertEqual(config_manager._config_etag, self.test_etag)
        self.assertDictEqual(config_manager._config, self.test_config_json)
        self.test_local_bucketing.store_config.assert_called_once_with(
            self.test_config_string
        )
        self.assertTrue(config_manager.is_initialized())
        mock_callback.assert_called_once()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    def test_close(self, mock_get_config):
        mock_get_config.return_value = (self.test_config_json, self.test_etag)
        self.test_options.config_polling_interval_ms = 500

        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )

        # sleep to allow polling thread to load the config
        time.sleep(0.1)

        config_manager.close()
        self.assertFalse(config_manager._polling_enabled)

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    def test_get_config_unchanged(self, mock_get_config):
        mock_get_config.return_value = (self.test_config_json, self.test_etag)

        self.test_options.config_polling_interval_ms = 200
        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )

        time.sleep(0.1)
        # stop the polling
        config_manager.close()

        self.test_local_bucketing.store_config.reset_mock()
        mock_get_config.return_value = (None, config_manager._config_etag)

        # trigger refresh of the config directly
        config_manager._get_config()

        # verify that the config was not updated
        self.assertEqual(config_manager._config_etag, self.test_etag)
        self.assertDictEqual(config_manager._config, self.test_config_json)
        self.test_local_bucketing.store_config.assert_not_called()


if __name__ == "__main__":
    unittest.main()
