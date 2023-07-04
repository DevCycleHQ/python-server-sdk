import logging
import time
import uuid
import unittest
from unittest.mock import MagicMock, patch

from devcycle_python_sdk import DevCycleLocalOptions
from devcycle_python_sdk.managers.event_queue_manager import (
    EventQueueManager,
    QueueFullError,
)
from devcycle_python_sdk.models.event import (
    FlushPayload,
    UserEventsBatchRecord,
    RequestEvent,
    DevCycleEvent,
    EventType,
)
from devcycle_python_sdk.models.user import DevCycleUser

from devcycle_python_sdk.exceptions import APIClientError, APIClientUnauthorizedError

logger = logging.getLogger(__name__)


class EventQueueManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sdk_key = "dvc_server_" + str(uuid.uuid4())

        # mock out the local bucketing to test event queue logic directly
        self.test_local_bucketing = MagicMock()
        self.test_local_bucketing.flush_event_queue = MagicMock()
        self.test_local_bucketing.flush_event_queue.return_value = []
        self.test_local_bucketing.get_event_queue_size = MagicMock()
        self.test_local_bucketing.get_event_queue_size.return_value = 0
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
                    user=DevCycleUser.from_json(
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

    def test_init(self):
        self.test_local_bucketing.flush_event_queue.return_value = []
        self.test_options.event_flush_interval_ms = 100
        manager = EventQueueManager(
            self.sdk_key, self.test_options, self.test_local_bucketing
        )
        self.assertTrue(manager._should_run())
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
        self.assertFalse(manager._should_run())
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

    def test_queue_event_bad_data(self):
        manager = EventQueueManager(
            self.sdk_key, self.test_options_no_thread, self.test_local_bucketing
        )
        with self.assertRaises(ValueError):
            manager.queue_event(user=None, event=None)

        with self.assertRaises(ValueError):
            manager.queue_event(user=DevCycleUser(user_id="test"), event=None)

        # Events must have a type
        with self.assertRaises(ValueError):
            manager.queue_event(
                user=DevCycleUser(user_id="test"), event=DevCycleEvent()
            )

    def test_queue_event(self):
        self.test_local_bucketing.queue_event = MagicMock()
        self.test_local_bucketing.get_event_queue_size.return_value = 1

        manager = EventQueueManager(
            self.sdk_key, self.test_options_no_thread, self.test_local_bucketing
        )
        DevCycleUser(user_id="test_user_id")
        event = DevCycleEvent(
            type=EventType.CustomEvent,
            target="string-var",
            value=1,
            metaData={"test": "test"},
        )
        manager.queue_event(DevCycleUser(user_id="test"), event)

        self.test_local_bucketing.queue_event.assert_called_once()
        self.assertEqual(self.test_local_bucketing.get_event_queue_size.call_count, 2)

    def test_check_queue_status(self):
        self.test_options_no_thread.flush_event_queue_size = 5
        self.test_options_no_thread.max_event_queue_size = 100

        manager = EventQueueManager(
            self.sdk_key, self.test_options_no_thread, self.test_local_bucketing
        )

        # queue empty, no issues
        self.test_local_bucketing.get_event_queue_size.return_value = 0
        manager._check_queue_status()
        self.test_local_bucketing.flush_event_queue.assert_not_called()

        # queue needs flush
        self.test_local_bucketing.flush_event_queue.reset_mock()
        self.test_local_bucketing.get_event_queue_size.return_value = 6
        manager._check_queue_status()
        self.test_local_bucketing.flush_event_queue.assert_called_once()

        # queue full - should flush and then throw error if queue is still full
        self.test_local_bucketing.flush_event_queue.reset_mock()

        self.test_local_bucketing.get_event_queue_size.return_value = 100
        with self.assertRaises(QueueFullError):
            manager._check_queue_status()
        self.test_local_bucketing.flush_event_queue.assert_called_once()

    def test_queue_aggregate_event_bad_data(self):
        manager = EventQueueManager(
            self.sdk_key, self.test_options_no_thread, self.test_local_bucketing
        )
        with self.assertRaises(ValueError):
            manager.queue_aggregate_event(event=None, bucketed_config=None)

        # agg event must have a type
        with self.assertRaises(ValueError):
            manager.queue_aggregate_event(event=DevCycleEvent(), bucketed_config=None)

        # agg event must have a target
        with self.assertRaises(ValueError):
            manager.queue_aggregate_event(
                event=DevCycleEvent(type=EventType.AggVariableDefaulted),
                bucketed_config=None,
            )

    def test_queue_aggregate_event(self):
        self.test_local_bucketing.queue_aggregate_event = MagicMock()
        self.test_local_bucketing.get_event_queue_size.return_value = 1

        manager = EventQueueManager(
            self.sdk_key, self.test_options_no_thread, self.test_local_bucketing
        )
        event = DevCycleEvent(
            type=EventType.AggVariableDefaulted,
            target="string-var",
            value=1,
            metaData={"test": "test"},
        )

        manager.queue_aggregate_event(event, None)

        self.test_local_bucketing.queue_aggregate_event.assert_called_once()
        self.assertEqual(self.test_local_bucketing.get_event_queue_size.call_count, 2)


if __name__ == "__main__":
    unittest.main()
