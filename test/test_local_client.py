import logging
import time
import unittest
import uuid
from unittest.mock import patch

import responses

from devcycle_python_sdk import DevCycleLocalClient, DevCycleLocalOptions
from devcycle_python_sdk.local_client import _validate_user, _validate_sdk_key
from devcycle_python_sdk.exceptions import MalformedConfigError
from devcycle_python_sdk.models.event import DevCycleEvent
from devcycle_python_sdk.models.feature import Feature
from devcycle_python_sdk.api.local_bucketing import LocalBucketing
from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.variable import Variable, TypeEnum
from test.fixture.data import small_config_json

logger = logging.getLogger(__name__)


class DevCycleLocalClientTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sdk_key = "dvc_server_949e4962-c624-4d20-a1ea-7f2501b2ba79"
        self.test_config_json = small_config_json()
        self.test_etag = "2f71454e-3279-4ca7-a8e7-802ce97bef43"

        config_url = "http://localhost/config/v1/server/" + self.sdk_key + ".json"

        responses.add(
            responses.GET,
            config_url,
            headers={"ETag": self.test_etag},
            json=self.test_config_json,
            status=200,
        )

        self.options = DevCycleLocalOptions(
            config_polling_interval_ms=5000,
            config_cdn_uri="http://localhost/",
            disable_custom_event_logging=True,
            disable_automatic_event_logging=True,
        )
        self.test_user = DevCycleUser(user_id="test_user_id")
        self.test_user_empty_id = DevCycleUser(user_id="")
        self.client = None

    def tearDown(self) -> None:
        if self.client:
            self.client.close()
        responses.reset()

    def setup_client(self):
        self.client = DevCycleLocalClient(self.sdk_key, self.options)
        while not self.client.is_initialized():
            time.sleep(0.05)

    def test_validate_sdk_key(self):
        with self.assertRaises(ValueError):
            _validate_sdk_key(None)

        with self.assertRaises(ValueError):
            _validate_sdk_key("")

        with self.assertRaises(ValueError):
            _validate_sdk_key("client_" + str(uuid.uuid4()))

        with self.assertRaises(ValueError):
            _validate_sdk_key(str(uuid.uuid4()))

    def test_validate_user(self):
        with self.assertRaises(ValueError):
            _validate_user(None)

        with self.assertRaises(ValueError):
            _validate_user(self.test_user_empty_id)

    @responses.activate
    def test_create_client_invalid_sdk_key(self):
        with self.assertRaises(ValueError):
            DevCycleLocalClient(None, None)

        with self.assertRaises(ValueError):
            DevCycleLocalClient("", None)

        with self.assertRaises(ValueError):
            DevCycleLocalClient("no prefix in key", None)

    @responses.activate
    def test_variable_bad_user(self):
        self.setup_client()

        with self.assertRaises(ValueError):
            self.client.variable(None, "strKey", "default_value")

        with self.assertRaises(ValueError):
            self.client.variable(self.test_user_empty_id, "strKey", "default_value")

    @responses.activate
    def test_variable_bad_key_and_value(self):
        self.setup_client()

        with self.assertRaises(ValueError):
            self.client.variable(self.test_user, None, "default_value")

        with self.assertRaises(ValueError):
            self.client.variable(self.test_user, "", "default_value")

        with self.assertRaises(ValueError):
            self.client.variable(self.test_user, "strKey", None)

    @responses.activate
    def test_all_variables_bad_user(self):
        self.setup_client()

        with self.assertRaises(ValueError):
            self.client.all_variables(None)

        with self.assertRaises(ValueError):
            self.client.all_variables(self.test_user_empty_id)

    @responses.activate
    def test_all_features_bad_user(self):
        self.setup_client()

        with self.assertRaises(ValueError):
            self.client.all_features(None)

        with self.assertRaises(ValueError):
            self.client.all_features(self.test_user_empty_id)

    @responses.activate
    def test_track_event_bad_user(self):
        self.setup_client()

        event = DevCycleEvent(
            type="user",
            target="test_target",
            value=42,
            metaData={"key": "value"},
        )

        with self.assertRaises(ValueError):
            self.client.track(None, event)

        with self.assertRaises(ValueError):
            self.client.track(self.test_user_empty_id, event)

    @responses.activate
    def test_track_bad_event(self):
        self.setup_client()

        with self.assertRaises(ValueError):
            self.client.track(self.test_user, None)

        event = DevCycleEvent(
            type=None,
            target="test_target",
            value=42,
            metaData={"key": "value"},
        )
        with self.assertRaises(ValueError):
            self.client.track(self.test_user, event)

        event = DevCycleEvent(
            type="",
            target="test_target",
            value=42,
            metaData={"key": "value"},
        )
        with self.assertRaises(ValueError):
            self.client.track(self.test_user, event)

    @responses.activate
    def test_set_client_custom_data(self):
        self.setup_client()

        # set the data without error
        client_custom_data = {
            "strProp": "strVal",
            "intProp": 1,
            "floatProp": 1.1,
            "boolProp": True,
            "nullProp": None,
        }
        self.client.set_client_custom_data(client_custom_data)

    @responses.activate
    def test_variable_default(self):
        self.setup_client()

        # try each default value data type and make sure it gets returned
        tests = [
            ("default_value", TypeEnum.STRING),
            (True, TypeEnum.BOOLEAN),
            (1000, TypeEnum.NUMBER),
            (0.0001, TypeEnum.NUMBER),
            ({"key": "value"}, TypeEnum.JSON),
        ]

        for test_value, value_type in tests:
            result = self.client.variable(self.test_user, "badKey", test_value)
            self.assertIsNotNone(result)
            self.assertEqual(result.key, "badKey")
            self.assertTrue(result.isDefaulted)
            self.assertEqual(result.defaultValue, test_value)
            self.assertEqual(result.value, test_value)
            self.assertEqual(result.type, value_type)

    @responses.activate
    def test_variable_with_bucketing(self):
        self.setup_client()

        user = DevCycleUser(user_id="1234")

        tests = [
            ("string-var", "default_value", "variationOn", TypeEnum.STRING),
            ("a-cool-new-feature", False, True, TypeEnum.BOOLEAN),
            ("num-var", 0, 12345, TypeEnum.NUMBER),
            (
                "json-var",
                {"default": "value"},
                {
                    "displayText": "This variation is on",
                    "showDialog": True,
                    "maxUsers": 100,
                },
                TypeEnum.JSON,
            ),
        ]

        for key, default_val, expected, var_type in tests:
            result = self.client.variable(user, key, default_val)
            self.assertIsNotNone(result, msg="Test key: " + key)
            self.assertEqual(result.key, key, msg="Test key: " + key)
            self.assertFalse(result.isDefaulted, msg="Test key: " + key)
            if var_type == TypeEnum.JSON:
                self.assertDictEqual(result.value, expected, msg="Test key: " + key)
            else:
                self.assertEqual(result.value, expected, msg="Test key: " + key)

    @responses.activate
    def test_variable_with_events(self):
        self.options.disable_automatic_event_logging = False
        self.options.disable_custom_event_logging = False
        self.options.event_flush_interval_ms = 0
        self.setup_client()
        user = DevCycleUser(user_id="1234")
        self.client.variable(user, "string-var", "default_value")

    @responses.activate
    def test_all_features(self):
        self.setup_client()

        user = DevCycleUser(user_id="1234")

        result = self.client.all_features(user)
        self.assertEqual(
            result,
            {
                "a-cool-new-feature": Feature(
                    _id="62fbf6566f1ba302829f9e32",
                    key="a-cool-new-feature",
                    type="release",
                    _variation="62fbf6566f1ba302829f9e39",
                    variationName="VariationOn",
                    variationKey="variation-on",
                    evalReason=None,
                )
            },
        )

    @responses.activate
    @patch.object(
        LocalBucketing,
        "generate_bucketed_config",
        side_effect=MalformedConfigError("bad config"),
    )
    def test_all_features_exception(self, _):
        self.setup_client()

        user = DevCycleUser(user_id="1234")

        result = self.client.all_features(user)
        self.assertEqual(result, {})

    @responses.activate
    def test_all_variables(self):
        self.setup_client()

        user = DevCycleUser(user_id="1234")

        result = self.client.all_variables(user)

        expected_variables = {
            "a-cool-new-feature": Variable(
                _id="62fbf6566f1ba302829f9e34",
                key="a-cool-new-feature",
                type="Boolean",
                value=True,
                isDefaulted=None,
                defaultValue=None,
                evalReason=None,
            ),
            "string-var": Variable(
                _id="63125320a4719939fd57cb2b",
                key="string-var",
                type="String",
                value="variationOn",
                isDefaulted=None,
                defaultValue=None,
                evalReason=None,
            ),
            "json-var": Variable(
                _id="64372363125123fca69d3f7b",
                key="json-var",
                type="JSON",
                value={
                    "displayText": "This variation is on",
                    "showDialog": True,
                    "maxUsers": 100,
                },
                isDefaulted=None,
                defaultValue=None,
                evalReason=None,
            ),
            "num-var": Variable(
                _id="65272363125123fca69d3a7d",
                key="num-var",
                type="Number",
                value=12345,
                isDefaulted=None,
                defaultValue=None,
                evalReason=None,
            ),
        }
        self.assertEqual(result, expected_variables)

    @responses.activate
    @patch.object(
        LocalBucketing,
        "generate_bucketed_config",
        side_effect=MalformedConfigError("bad config"),
    )
    def test_all_variables_exception(self, _):
        self.setup_client()

        user = DevCycleUser(user_id="1234")

        result = self.client.all_variables(user)
        self.assertEqual(result, {})


def _benchmark_variable_call(client: DevCycleLocalClient, user: DevCycleUser, key: str):
    return client.variable(user, key, "default_value")


@responses.activate
def test_benchmark_variable_call(benchmark):
    sdk_key = "dvc_server_949e4962-c624-4d20-a1ea-7f2501b2ba79"
    test_config_json = small_config_json()
    test_etag = "2f71454e-3279-4ca7-a8e7-802ce97bef43"

    config_url = "http://localhost/config/v1/server/" + sdk_key + ".json"

    responses.add(
        responses.GET,
        config_url,
        headers={"ETag": test_etag},
        json=test_config_json,
        status=200,
    )

    options = DevCycleLocalOptions(
        config_polling_interval_ms=5000,
        config_cdn_uri="http://localhost/",
        disable_custom_event_logging=True,
        disable_automatic_event_logging=True,
    )
    user = DevCycleUser(user_id="test_user_id")

    client = DevCycleLocalClient(sdk_key, options)
    while not client.is_initialized():
        time.sleep(0.05)

    # benchmark is a pytest fixture provided by pytest-benchmark that handles timing the provided callable
    result = benchmark(_benchmark_variable_call, client, user, "string-var")

    assert result is not None
    assert result.key == "string-var"
    assert result.isDefaulted is False
    assert result.value == "variationOn"
    assert result.type == TypeEnum.STRING


if __name__ == "__main__":
    unittest.main()
