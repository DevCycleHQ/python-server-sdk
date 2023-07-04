import json
import logging
import requests
import responses
from responses.registries import OrderedRegistry
import unittest
import uuid

from devcycle_python_sdk.api.bucketing_client import BucketingAPIClient
from devcycle_python_sdk.exceptions import (
    CloudClientError,
    CloudClientUnauthorizedError,
    NotFoundError,
)
from devcycle_python_sdk.options import DevCycleCloudOptions
from devcycle_python_sdk.models.event import DevCycleEvent
from devcycle_python_sdk.models.feature import Feature
from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.variable import Variable

logger = logging.getLogger(__name__)


class BucketingClientTest(unittest.TestCase):
    def setUp(self) -> None:
        sdk_key = "dvc_server_" + str(uuid.uuid4())
        options = DevCycleCloudOptions(retry_delay=0)
        self.test_client = BucketingAPIClient(sdk_key, options)
        self.test_user = DevCycleUser(user_id="test_user_id")

    @responses.activate
    def test_variable(self):
        responses.add(
            responses.POST,
            "https://bucketing-api.devcycle.com/v1/variables/variable-key",
            json={
                "_id": "variable_id",
                "key": "variable-key",
                "type": "variable-type",
                "value": "hello world",
            },
        )
        result = self.test_client.variable("variable-key", self.test_user)

        self.assertEqual(
            result,
            Variable(
                _id="variable_id",
                key="variable-key",
                type="variable-type",
                value="hello world",
            ),
        )

    @responses.activate(registry=OrderedRegistry)
    def test_variable_retries(self):
        for i in range(self.test_client.options.request_retries):
            responses.add(
                responses.POST,
                "https://bucketing-api.devcycle.com/v1/variables/variable-key",
                status=500,
            )
        responses.add(
            responses.POST,
            "https://bucketing-api.devcycle.com/v1/variables/variable-key",
            json={
                "_id": "variable_id",
                "key": "variable-key",
                "type": "variable-type",
                "value": "hello world",
            },
        )
        result = self.test_client.variable("variable-key", self.test_user)
        self.assertEqual(
            result,
            Variable(
                _id="variable_id",
                key="variable-key",
                type="variable-type",
                value="hello world",
            ),
        )

    @responses.activate(registry=OrderedRegistry)
    def test_variable_retries_network_error(self):
        responses.add(
            responses.POST,
            "https://bucketing-api.devcycle.com/v1/variables/variable-key",
            body=requests.exceptions.ConnectionError("Network Error"),
        )
        responses.add(
            responses.POST,
            "https://bucketing-api.devcycle.com/v1/variables/variable-key",
            json={
                "_id": "variable_id",
                "key": "variable-key",
                "type": "variable-type",
                "value": "hello world",
            },
        )
        result = self.test_client.variable("variable-key", self.test_user)
        self.assertEqual(
            result,
            Variable(
                _id="variable_id",
                key="variable-key",
                type="variable-type",
                value="hello world",
            ),
        )

    @responses.activate
    def test_variable_retries_exceeded(self):
        for i in range(self.test_client.options.request_retries + 1):
            responses.add(
                responses.POST,
                "https://bucketing-api.devcycle.com/v1/variables/variable-key",
                status=500,
            )
        with self.assertRaises(CloudClientError):
            self.test_client.variable("variable-key", self.test_user)

    @responses.activate
    def test_variable_unauthorized(self):
        for i in range(2):
            responses.add(
                responses.POST,
                "https://bucketing-api.devcycle.com/v1/variables/variable-key",
                status=401,
            )
        with self.assertRaises(CloudClientUnauthorizedError):
            self.test_client.variable("variable-key", self.test_user)

    @responses.activate
    def test_variable_not_found(self):
        for i in range(2):
            responses.add(
                responses.POST,
                "https://bucketing-api.devcycle.com/v1/variables/variable-key",
                status=404,
            )
        with self.assertRaises(NotFoundError):
            self.test_client.variable("variable-key", self.test_user)

    @responses.activate
    def test_variables(self):
        responses.add(
            responses.POST,
            "https://bucketing-api.devcycle.com/v1/variables",
            json={
                "variable-1": {
                    "_id": "variable_id",
                    "key": "variable-key",
                    "type": "variable-type",
                    "value": "hello world",
                },
            },
        )
        result = self.test_client.variables(self.test_user)

        self.assertEqual(
            result,
            {
                "variable-1": Variable(
                    _id="variable_id",
                    key="variable-key",
                    type="variable-type",
                    value="hello world",
                    isDefaulted=None,
                )
            },
        )

    @responses.activate
    def test_features(self):
        responses.add(
            responses.POST,
            "https://bucketing-api.devcycle.com/v1/features",
            json={
                "feature-1": {
                    "_id": "variable_id",
                    "key": "variable-key",
                    "type": "feature-type",
                    "_variation": "variation",
                    "variationName": "variation-name",
                    "variationKey": "variation-key",
                    "evalReason": "eval-reason",
                },
            },
        )
        result = self.test_client.features(self.test_user)

        self.assertEqual(
            result,
            {
                "feature-1": Feature(
                    _id="variable_id",
                    key="variable-key",
                    type="feature-type",
                    _variation="variation",
                    variationName="variation-name",
                    variationKey="variation-key",
                    evalReason="eval-reason",
                )
            },
        )

    @responses.activate
    def test_track(self):
        responses.add(
            responses.POST,
            "https://bucketing-api.devcycle.com/v1/track",
            json={
                "message": "success",
            },
        )
        result = self.test_client.track(
            self.test_user,
            events=[
                DevCycleEvent(
                    type="sample-event",
                )
            ],
        )
        self.assertEqual(result, "success")
        data = json.loads(responses.calls[0].request.body)
        self.assertTrue(type(data["events"][0]["date"]) == int)
        self.assertEqual(len(data["events"]), 1)
        self.assertEqual(data["events"][0]["type"], "sample-event")


if __name__ == "__main__":
    unittest.main()
