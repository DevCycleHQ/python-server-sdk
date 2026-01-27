import json
import logging
import time
import unittest
import uuid
import threading
from datetime import datetime
from email.utils import formatdate
from time import mktime
from unittest.mock import patch, MagicMock, Mock, PropertyMock

from devcycle_python_sdk import DevCycleLocalOptions
from devcycle_python_sdk.managers.config_manager import EnvironmentConfigManager
from test.fixture.data import small_config_json

logger = logging.getLogger(__name__)


class EnvironmentConfigManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sdk_key = "dvc_server_" + str(uuid.uuid4())
        self.test_local_bucketing = MagicMock()
        self.test_options = DevCycleLocalOptions(
            config_polling_interval_ms=500, disable_realtime_updates=True
        )

        now = datetime.now()
        stamp = mktime(now.timetuple())
        self.test_lastmodified = formatdate(timeval=stamp, localtime=False, usegmt=True)
        self.test_etag = str(uuid.uuid4())
        self.test_config_json = small_config_json()
        self.test_config_string = json.dumps(self.test_config_json)

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    def test_init(self, mock_get_config):
        mock_get_config.return_value = (
            self.test_config_json,
            self.test_etag,
            self.test_lastmodified,
        )
        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )

        # sleep to allow polling thread to load the config
        time.sleep(0.1)
        mock_get_config.assert_called_once_with(config_etag=None, last_modified=None)

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
        mock_get_config.return_value = (
            self.test_config_json,
            self.test_etag,
            self.test_lastmodified,
        )

        mock_callback = MagicMock()

        self.test_options.on_client_initialized = mock_callback

        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)
        mock_get_config.assert_called_once_with(config_etag=None, last_modified=None)
        self.assertEqual(config_manager._config_etag, self.test_etag)
        self.assertDictEqual(config_manager._config, self.test_config_json)
        self.test_local_bucketing.store_config.assert_called_once_with(
            self.test_config_string
        )
        self.assertTrue(config_manager.is_initialized())
        mock_callback.assert_called_once()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    def test_init_with_client_callback_with_error(self, mock_get_config):
        mock_get_config.return_value = (
            self.test_config_json,
            self.test_etag,
            self.test_lastmodified,
        )
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
        mock_get_config.assert_called_once_with(config_etag=None, last_modified=None)
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
        mock_get_config.return_value = (
            self.test_config_json,
            self.test_etag,
            self.test_lastmodified,
        )

        self.test_options.config_polling_interval_ms = 200
        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )

        time.sleep(0.1)
        # stop the polling
        config_manager.close()

        self.test_local_bucketing.store_config.reset_mock()
        mock_get_config.return_value = (None, config_manager._config_etag, None)

        # trigger refresh of the config directly
        config_manager._get_config()

        # verify that the config was not updated
        self.assertEqual(config_manager._config_etag, self.test_etag)
        self.assertDictEqual(config_manager._config, self.test_config_json)
        self.test_local_bucketing.store_config.assert_not_called()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    @patch("devcycle_python_sdk.managers.config_manager.SSEManager")
    def test_recreate_sse_connection_clears_old_manager(self, mock_sse_manager_class, mock_get_config):
        """Test that _recreate_sse_connection sets _sse_manager to None before blocking operations."""
        mock_get_config.return_value = (
            self.test_config_json,
            self.test_etag,
            self.test_lastmodified,
        )
        
        # Enable realtime updates for this test
        self.test_options.disable_realtime_updates = False
        
        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)
        
        # Create a mock SSE manager with a thread
        mock_old_sse = MagicMock()
        mock_old_sse.client = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        
        # Track when join is called and what _sse_manager is at that point
        manager_during_join = []
        
        def track_join(timeout=None):
            manager_during_join.append(config_manager._sse_manager)
        
        mock_thread.join = track_join
        mock_old_sse.read_thread = mock_thread
        
        config_manager._sse_manager = mock_old_sse
        
        # Call _recreate_sse_connection
        config_manager._recreate_sse_connection()
        
        # Verify that _sse_manager was None during the join (blocking operation)
        self.assertEqual(len(manager_during_join), 1)
        self.assertIsNone(manager_during_join[0])
        
        # Verify old manager was closed
        mock_old_sse.client.close.assert_called_once()
        
        config_manager.close()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    @patch("devcycle_python_sdk.managers.config_manager.SSEManager")
    def test_recreate_sse_connection_uses_latest_config(self, mock_sse_manager_class, mock_get_config):
        """Test that _recreate_sse_connection uses the latest config when re-acquiring lock."""
        initial_config = self.test_config_json.copy()
        mock_get_config.return_value = (
            initial_config,
            self.test_etag,
            self.test_lastmodified,
        )
        
        # Enable realtime updates
        self.test_options.disable_realtime_updates = False
        
        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)
        
        # Create a mock SSE manager
        mock_old_sse = MagicMock()
        mock_old_sse.client = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        
        # Update config during the blocking operation
        updated_config = initial_config.copy()
        updated_config["updated"] = True
        
        def delayed_config_update(timeout=None):
            # Simulate config update happening during join
            config_manager._config = updated_config
            time.sleep(0.05)
        
        mock_thread.join = delayed_config_update
        mock_old_sse.read_thread = mock_thread
        
        config_manager._sse_manager = mock_old_sse
        
        # Reset the mock after initialization
        mock_sse_manager_class.reset_mock()
        
        # Create a new mock SSE manager for the recreation
        mock_new_sse = MagicMock()
        mock_sse_manager_class.return_value = mock_new_sse
        
        # Call _recreate_sse_connection
        config_manager._recreate_sse_connection()
        
        # Verify the new SSE manager was created and updated with the latest config
        mock_sse_manager_class.assert_called_once()
        mock_new_sse.update.assert_called_once()
        
        # The config passed to update should be the updated one
        call_args = mock_new_sse.update.call_args[0][0]
        self.assertIn("updated", call_args)
        self.assertTrue(call_args["updated"])
        
        config_manager.close()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    @patch("devcycle_python_sdk.managers.config_manager.SSEManager")
    def test_recreate_sse_connection_concurrent_calls(self, mock_sse_manager_class, mock_get_config):
        """Test that concurrent calls to _recreate_sse_connection are handled safely."""
        mock_get_config.return_value = (
            self.test_config_json,
            self.test_etag,
            self.test_lastmodified,
        )
        
        # Enable realtime updates
        self.test_options.disable_realtime_updates = False
        
        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)
        
        # Create a mock SSE manager with slow close/join
        mock_old_sse = MagicMock()
        mock_old_sse.client = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        
        # Make join slow to allow concurrent calls
        def slow_join(timeout=None):
            time.sleep(0.2)
        
        mock_thread.join = slow_join
        mock_old_sse.read_thread = mock_thread
        
        config_manager._sse_manager = mock_old_sse
        
        # Reset the mock after initialization  
        mock_sse_manager_class.reset_mock()
        
        # Mock new SSE managers
        mock_new_sse_1 = MagicMock()
        mock_new_sse_2 = MagicMock()
        mock_sse_manager_class.side_effect = [mock_new_sse_1, mock_new_sse_2]
        
        # Track completion
        results = []
        
        def call_recreate(index):
            try:
                config_manager._recreate_sse_connection()
                results.append(f"completed_{index}")
            except Exception as e:
                results.append(f"error_{index}: {e}")
        
        # Start two concurrent recreate calls
        thread1 = threading.Thread(target=call_recreate, args=(1,))
        thread2 = threading.Thread(target=call_recreate, args=(2,))
        
        thread1.start()
        time.sleep(0.05)  # Small delay to ensure thread1 starts first
        thread2.start()
        
        thread1.join(timeout=2.0)
        thread2.join(timeout=2.0)
        
        # Both should complete without errors
        self.assertEqual(len(results), 2)
        self.assertIn("completed_1", results)
        self.assertIn("completed_2", results)
        
        # At least one SSE manager should be created
        self.assertGreaterEqual(mock_sse_manager_class.call_count, 1)
        
        config_manager.close()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    @patch("devcycle_python_sdk.managers.config_manager.SSEManager")
    def test_recreate_sse_connection_skips_if_config_cleared(self, mock_sse_manager_class, mock_get_config):
        """Test that _recreate_sse_connection skips if config is cleared during reconnection."""
        mock_get_config.return_value = (
            self.test_config_json,
            self.test_etag,
            self.test_lastmodified,
        )
        
        # Enable realtime updates
        self.test_options.disable_realtime_updates = False
        
        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)
        
        # Create a mock SSE manager
        mock_old_sse = MagicMock()
        mock_old_sse.client = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = True
        
        # Clear config during join
        def clear_config_during_join(timeout=None):
            config_manager._config = None
            time.sleep(0.05)
        
        mock_thread.join = clear_config_during_join
        mock_old_sse.read_thread = mock_thread
        
        config_manager._sse_manager = mock_old_sse
        
        # Reset the mock after initialization
        mock_sse_manager_class.reset_mock()
        
        # Call _recreate_sse_connection
        config_manager._recreate_sse_connection()
        
        # Verify old manager was closed
        mock_old_sse.client.close.assert_called_once()
        
        # Verify no new SSE manager was created (because config was None)
        mock_sse_manager_class.assert_not_called()
        
        # _sse_manager should still be None
        self.assertIsNone(config_manager._sse_manager)
        
        config_manager.close()


if __name__ == "__main__":
    unittest.main()
