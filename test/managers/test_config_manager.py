import json
import logging
import time
import unittest
import uuid
from datetime import datetime
from email.utils import formatdate
from time import mktime
from unittest.mock import patch, MagicMock

import ld_eventsource.actions

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


class SSEReconnectionBackoffTest(unittest.TestCase):
    """Tests for SSE exponential backoff reconnection behavior"""

    def setUp(self) -> None:
        self.sdk_key = "dvc_server_" + str(uuid.uuid4())
        self.test_local_bucketing = MagicMock()
        self.test_options = DevCycleLocalOptions(
            config_polling_interval_ms=500, disable_realtime_updates=False
        )
        self.test_config_json = small_config_json()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    @patch("devcycle_python_sdk.managers.config_manager.SSEManager")
    @patch("threading.Thread")
    @patch("time.time")
    def test_first_sse_error_triggers_immediate_reconnection(
        self, mock_time, mock_thread, mock_sse_manager, mock_get_config
    ):
        """First error should trigger reconnection with min backoff (5s)"""
        mock_time.return_value = 1000.0
        mock_get_config.return_value = (self.test_config_json, "etag", None)

        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)

        # Simulate first SSE error
        error = ld_eventsource.actions.Fault(error=Exception("Connection failed"))
        config_manager.sse_error(error)

        # Verify reconnection attempt counter incremented
        self.assertEqual(config_manager._sse_reconnect_attempts, 1)
        # Verify reconnecting flag set
        self.assertTrue(config_manager._sse_reconnecting)
        # Verify thread spawned with min backoff (5.0s)
        mock_thread.assert_called_once()
        call_args = mock_thread.call_args
        self.assertEqual(call_args[1]["args"][0], 5.0)  # backoff_interval

        config_manager.close()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    @patch("devcycle_python_sdk.managers.config_manager.SSEManager")
    @patch("threading.Thread")
    @patch("time.time")
    def test_exponential_backoff_calculation(
        self, mock_time, mock_thread, mock_sse_manager, mock_get_config
    ):
        """Verify exponential backoff: 5s, 10s, 20s, 40s, etc."""
        mock_time.return_value = 1000.0
        mock_get_config.return_value = (self.test_config_json, "etag", None)

        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)

        error = ld_eventsource.actions.Fault(error=Exception("Connection failed"))

        # First error: 5s backoff (2^0 * 5)
        config_manager.sse_error(error)
        self.assertEqual(config_manager._sse_reconnect_attempts, 1)
        self.assertEqual(mock_thread.call_args[1]["args"][0], 5.0)

        # Simulate reconnect completing
        config_manager._sse_reconnecting = False
        mock_time.return_value += 10.0  # Advance time beyond backoff

        # Second error: 10s backoff (2^1 * 5)
        config_manager.sse_error(error)
        self.assertEqual(config_manager._sse_reconnect_attempts, 2)
        self.assertEqual(mock_thread.call_args[1]["args"][0], 10.0)

        # Simulate reconnect completing
        config_manager._sse_reconnecting = False
        mock_time.return_value += 15.0

        # Third error: 20s backoff (2^2 * 5)
        config_manager.sse_error(error)
        self.assertEqual(config_manager._sse_reconnect_attempts, 3)
        self.assertEqual(mock_thread.call_args[1]["args"][0], 20.0)

        config_manager.close()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    @patch("devcycle_python_sdk.managers.config_manager.SSEManager")
    @patch("threading.Thread")
    @patch("time.time")
    def test_backoff_caps_at_max_interval(
        self, mock_time, mock_thread, mock_sse_manager, mock_get_config
    ):
        """Verify backoff caps at max interval (300s)"""
        mock_time.return_value = 1000.0
        mock_get_config.return_value = (self.test_config_json, "etag", None)

        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)

        error = ld_eventsource.actions.Fault(error=Exception("Connection failed"))

        # Simulate many failures to reach max backoff
        # 2^6 * 5 = 320s > 300s (max), so should cap at 300s
        config_manager._sse_reconnect_attempts = 6
        config_manager.sse_error(error)

        # Should be capped at 300s
        self.assertEqual(mock_thread.call_args[1]["args"][0], 300.0)

        config_manager.close()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    @patch("devcycle_python_sdk.managers.config_manager.SSEManager")
    @patch("threading.Thread")
    def test_concurrent_errors_only_spawn_one_reconnection(
        self, mock_thread, mock_sse_manager, mock_get_config
    ):
        """Multiple rapid errors should only spawn one reconnection thread"""
        mock_get_config.return_value = (self.test_config_json, "etag", None)

        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)

        error = ld_eventsource.actions.Fault(error=Exception("Connection failed"))

        # First error spawns reconnection
        config_manager.sse_error(error)
        self.assertEqual(mock_thread.call_count, 1)
        self.assertTrue(config_manager._sse_reconnecting)

        # Second error while reconnecting should be skipped
        config_manager.sse_error(error)
        # Still only 1 thread spawned
        self.assertEqual(mock_thread.call_count, 1)

        config_manager.close()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    @patch("devcycle_python_sdk.managers.config_manager.SSEManager")
    @patch("threading.Thread")
    @patch("time.time")
    def test_error_within_backoff_uses_remaining_time(
        self, mock_time, mock_thread, mock_sse_manager, mock_get_config
    ):
        """Error within backoff period should schedule reconnect with remaining time"""
        mock_time.return_value = 1000.0
        mock_get_config.return_value = (self.test_config_json, "etag", None)

        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)

        error = ld_eventsource.actions.Fault(error=Exception("Connection failed"))

        # First error at t=1000, backoff=5s
        config_manager.sse_error(error)
        self.assertEqual(mock_thread.call_args[1]["args"][0], 5.0)

        # Simulate reconnect completing and updating timestamp
        config_manager._sse_reconnecting = False
        config_manager._last_reconnect_attempt_time = (
            1005.0  # Simulates reconnect at t=1005
        )

        # Second error at t=1008 (3s after reconnect, within 10s backoff)
        mock_time.return_value = 1008.0
        config_manager.sse_error(error)

        # Should use remaining time: 10s backoff - 3s elapsed = 7s
        self.assertAlmostEqual(mock_thread.call_args[1]["args"][0], 7.0, places=1)

        config_manager.close()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    @patch("devcycle_python_sdk.managers.config_manager.SSEManager")
    def test_successful_connection_resets_attempts(
        self, mock_sse_manager, mock_get_config
    ):
        """Successful SSE connection should reset reconnection attempts"""
        mock_get_config.return_value = (self.test_config_json, "etag", None)

        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)

        # Simulate multiple failures
        config_manager._sse_reconnect_attempts = 5
        config_manager._sse_reconnecting = True
        config_manager._last_reconnect_attempt_time = 1000.0

        # Simulate successful ping message (which resets attempts)
        message = ld_eventsource.actions.Event(
            event="message",
            data='{"data": "{\\"type\\": \\"ping\\", \\"lastModified\\": 1234567890000}"}',
        )
        config_manager.sse_message(message)

        # Attempts should be reset
        self.assertEqual(config_manager._sse_reconnect_attempts, 0)

        config_manager.close()

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    @patch("devcycle_python_sdk.managers.config_manager.SSEManager")
    def test_successful_state_resets_reconnection_flags(
        self, mock_sse_manager, mock_get_config
    ):
        """Successful SSE state should clear reconnection flags"""
        mock_get_config.return_value = (self.test_config_json, "etag", None)

        config_manager = EnvironmentConfigManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        time.sleep(0.1)

        # Simulate reconnection in progress
        config_manager._sse_reconnecting = True
        config_manager._last_reconnect_attempt_time = 1000.0
        config_manager._sse_connected = False

        # Simulate successful connection
        state = ld_eventsource.actions.Start()
        config_manager.sse_state(state)

        # Should clear reconnection state
        self.assertFalse(config_manager._sse_reconnecting)
        self.assertIsNone(config_manager._last_reconnect_attempt_time)
        self.assertTrue(config_manager._sse_connected)

        config_manager.close()


if __name__ == "__main__":
    unittest.main()
