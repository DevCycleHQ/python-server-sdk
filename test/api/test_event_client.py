import logging
import unittest
import uuid
from http import HTTPStatus

import responses
from responses.registries import OrderedRegistry

from devcycle_python_sdk.api.event_client import EventAPIClient
from devcycle_python_sdk.options import DevCycleLocalOptions
from devcycle_python_sdk.exceptions import (
    APIClientError,
    APIClientUnauthorizedError,
    NotFoundError,
)
from devcycle_python_sdk.models.event import (
    UserEventsBatchRecord,
    RequestEvent,
    EventType,
)
from devcycle_python_sdk.models.user import DevCycleUser

logger = logging.getLogger(__name__)


class EventAPIClientTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sdk_key = "dvc_server_" + str(uuid.uuid4())
        options = DevCycleLocalOptions(events_api_uri="http://localhost:8080")

        self.test_client = EventAPIClient(self.sdk_key, options)
        self.test_batch_url = "http://localhost:8080/v1/events/batch"

        self.test_user = DevCycleUser(user_id="123")
        events = [
            RequestEvent(
                type=EventType.VariableDefaulted,
                user_id="123",
                date="2023-06-27T12:50:19.871Z",
                clientDate="2023-06-27T12:50:19.871Z",
            )
        ]
        self.test_batch = [UserEventsBatchRecord(user=self.test_user, events=events)]

    def test_url(self):
        self.assertEqual(self.test_client.batch_url, self.test_batch_url)

    @responses.activate
    def test_publish_events(self):
        responses.add(
            responses.POST,
            self.test_batch_url,
            json={"message": "Successfully received 1 event batches."},
        )

        message = self.test_client.publish_events(self.test_batch)
        self.assertEqual(message, "Successfully received 1 event batches.")

    @responses.activate
    def test_publish_events_empty_batch(self):
        responses.add(
            responses.POST,
            self.test_batch_url,
            json={"message": "Successfully received 1 event batches."},
        )
        message = self.test_client.publish_events([])
        self.assertEqual(message, "Successfully received 1 event batches.")

    @responses.activate(registry=OrderedRegistry)
    def test_publish_events_retries_exceeded(self):
        for i in range(2):
            responses.add(
                responses.POST,
                self.test_batch_url,
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        with self.assertRaises(APIClientError):
            self.test_client.publish_events(self.test_batch)

    @responses.activate
    def test_publish_events_not_found(self):
        for i in range(2):
            responses.add(
                responses.POST,
                self.test_batch_url,
                status=HTTPStatus.NOT_FOUND,
            )
        with self.assertRaises(NotFoundError):
            self.test_client.publish_events(self.test_batch)

    @responses.activate
    def test_publish_events_unauthorized(self):
        for i in range(2):
            responses.add(
                responses.POST,
                self.test_batch_url,
                status=HTTPStatus.UNAUTHORIZED,
            )
        with self.assertRaises(APIClientUnauthorizedError):
            self.test_client.publish_events(self.test_batch)
