import logging
import time
import uuid
import unittest
from unittest.mock import MagicMock, patch

from devcycle_python_sdk import DevCycleLocalOptions
from devcycle_python_sdk.managers.event_queue_manager import EventQueueManager
from devcycle_python_sdk.models.event import (
    FlushPayload,
    UserEventsBatchRecord,
    RequestEvent,
)
from devcycle_python_sdk.models.user import User

from devcycle_python_sdk.exceptions import APIClientError, APIClientUnauthorizedError

logger = logging.getLogger(__name__)


class EventQueueManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sdk_key = "dvc_server_" + str(uuid.uuid4())
        self.test_local_bucketing = MagicMock()
        self.test_local_bucketing.flush_event_queue = MagicMock()
        self.test_local_bucketing.flush_event_queue.return_value = []
        self.test_local_bucketing.on_event_payload_success = MagicMock()
        self.test_local_bucketing.on_event_payload_failure = MagicMock()

        self.test_options = DevCycleLocalOptions(
            disable_automatic_event_logging=False, disable_custom_event_logging=False
        )
        self.test_options_no_thread = DevCycleLocalOptions(
            disable_automatic_event_logging=True, disable_custom_event_logging=True
        )
        self.test_payload = FlushPayload(
            payloadId="123",
            records=[
                UserEventsBatchRecord(
                    user=User.from_json(
                        {
                            "user_id": "999-000-111",
                            "createdDate": "1970-01-20T12:50:19.871Z",
                            "lastSeenDate": "1970-01-20T12:50:19.871Z",
                            "platform": "Python",
                            "platformVersion": "3.11.4",
                            "sdkType": "local",
                            "sdkVersion": "2.0.1",
                            "hostname": "Chris-DevCycle-MacBook.local",
                        }
                    ),
                    events=[
                        RequestEvent.from_json(
                            {
                                "type": "aggVariableEvaluated",
                                "target": "string-var",
                                "user_id": "999-000-111",
                                "date": "1970-01-20T12:50:19.871Z",
                                "clientDate": "1970-01-20T12:50:19.871Z",
                                "value": 1.0,
                                "featureVars": {},
                                "metaData": {
                                    "_feature": "62fbf6566f1ba302829f9e32",
                                    "_variation": "62fbf6566f1ba302829f9e39",
                                },
                            }
                        )
                    ],
                )
            ],
            eventCount=1,
        )

    def tearDown(self) -> None:
        pass

    def test_init(self):
        self.test_local_bucketing.flush_event_queue.return_value = []
        self.test_options.event_flush_interval_ms = 100
        manager = EventQueueManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        self.assertTrue(manager._processing_enabled)
        self.assertTrue(manager.is_alive())
        self.assertTrue(manager.daemon)

    def test_close(self):
        self.test_local_bucketing.flush_event_queue.return_value = []
        self.test_options.event_flush_interval_ms = 100
        manager = EventQueueManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )

        manager.close()
        # let the thread wake up from sleep and react to the close
        time.sleep(0.5)
        self.assertFalse(manager._processing_enabled)
        self.assertFalse(manager.is_alive())

    @patch("devcycle_python_sdk.api.event_client.EventAPIClient.publish_events")
    def test_publish_event_payload_retryable_api_error(self, mock_publish_events):
        self.test_local_bucketing.on_event_payload_success = MagicMock()
        self.test_local_bucketing.on_event_payload_failure = MagicMock()

        mock_publish_events.side_effect = APIClientError("Some retryable error")

        manager = EventQueueManager(
            self.sdk_key, self.test_options_no_thread, self.test_local_bucketing
        )
        manager._publish_event_payload(self.test_payload)

        # should try and publish events, get the error and then report the failure to local bucketing
        mock_publish_events.assert_called_once()
        self.test_local_bucketing.on_event_payload_failure.assert_called_with(
            self.test_payload.payloadId, True
        )
        self.test_local_bucketing.on_event_payload_success.assert_not_called()

    @patch("devcycle_python_sdk.api.event_client.EventAPIClient.publish_events")
    def test_publish_event_payload_non_retryable_api_error(self, mock_publish_events):
        mock_publish_events.side_effect = APIClientUnauthorizedError(
            "Some retryable error"
        )

        manager = EventQueueManager(
            self.sdk_key, self.test_options_no_thread, self.test_local_bucketing
        )
        manager._publish_event_payload(self.test_payload)

        # should try and publish events, get the error and then report the failure to local bucketing
        mock_publish_events.assert_called_once()
        self.test_local_bucketing.on_event_payload_failure.assert_called_with(
            self.test_payload.payloadId, False
        )
        self.test_local_bucketing.on_event_payload_success.assert_not_called()

    @patch("devcycle_python_sdk.api.event_client.EventAPIClient.publish_events")
    def test_flush_events_no_events(self, mock_publish_events):
        self.test_local_bucketing.flush_event_queue = MagicMock()
        self.test_local_bucketing.flush_event_queue.return_value = []

        manager = EventQueueManager(
            self.sdk_key, self.test_options_no_thread, self.test_local_bucketing
        )
        manager._flush_events()

        self.test_local_bucketing.flush_event_queue.assert_called_once()
        mock_publish_events.assert_not_called()

    @patch("devcycle_python_sdk.api.event_client.EventAPIClient.publish_events")
    def test_flush_events(self, mock_publish_events):
        self.test_local_bucketing.flush_event_queue.return_value = [self.test_payload]

        manager = EventQueueManager(
            self.sdk_key, self.test_options_no_thread, self.test_local_bucketing
        )
        result = manager._flush_events()

        self.assertEqual(result, 1)
        self.test_local_bucketing.flush_event_queue.assert_called_once()
        mock_publish_events.assert_called_once()
        self.test_local_bucketing.on_event_payload_success.assert_called_once()


if __name__ == "__main__":
    unittest.main()
