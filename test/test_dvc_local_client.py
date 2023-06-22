import logging
import unittest
import uuid
import responses
import time

from devcycle_python_sdk import DevCycleLocalClient, DevCycleLocalOptions
from devcycle_python_sdk.dvc_local_client import _validate_user, _validate_sdk_key, _add_platform_data_to_user
from devcycle_python_sdk.models.event import Event
from devcycle_python_sdk.models.user import User
from test.fixture.data import small_config_json

logger = logging.getLogger(__name__)


class DVCLocalClientTest(unittest.TestCase):

    def setUp(self) -> None:
        self.sdk_key = "dvc_server_949e4962-c624-4d20-a1ea-7f2501b2ba79"
        self.test_config_json = small_config_json()
        self.test_etag = "2f71454e-3279-4ca7-a8e7-802ce97bef43"

        config_url = "http://localhost/v1/server/" + self.sdk_key + ".json"
        responses.add(
            responses.GET,
            config_url,
            headers={"ETag": self.test_etag},
            json=self.test_config_json,
            status=200,
        )

        self.options = DevCycleLocalOptions(config_polling_interval_ms=1000, config_cdn_uri="http://localhost/")

        self.test_user = User(user_id="test_user_id")
        self.test_user_empty_id = User(user_id="")
        self.client = None

    def tearDown(self) -> None:
        if self.client:
            self.client.close()

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
        self.client = DevCycleLocalClient(self.sdk_key, self.options)
        while not self.client.is_initialized():
            time.sleep(0.1)

        with self.assertRaises(ValueError):
            self.client.variable(None, "strKey", "default_value")

        with self.assertRaises(ValueError):
            self.client.variable(
                self.test_user_empty_id, "strKey", "default_value"
            )

    @responses.activate
    def test_variable_bad_key_and_value(self):
        self.client = DevCycleLocalClient(self.sdk_key, self.options)
        while not self.client.is_initialized():
            time.sleep(0.1)

        with self.assertRaises(ValueError):
            self.client.variable(self.test_user, None, "default_value")

        with self.assertRaises(ValueError):
            self.client.variable(self.test_user, "", "default_value")

        with self.assertRaises(ValueError):
            self.client.variable(self.test_user, "strKey", None)

    @responses.activate
    def test_all_variables_bad_user(self):
        self.client = DevCycleLocalClient(self.sdk_key, self.options)

        with self.assertRaises(ValueError):
            self.client.all_variables(None)

        with self.assertRaises(ValueError):
            self.client.all_variables(self.test_user_empty_id)

    @responses.activate
    def test_all_features_bad_user(self):
        self.client = DevCycleLocalClient(self.sdk_key, self.options)
        with self.assertRaises(ValueError):
            self.client.all_features(None)

        with self.assertRaises(ValueError):
            self.client.all_features(self.test_user_empty_id)

    @responses.activate
    def test_track_event_bad_user(self):
        self.client = DevCycleLocalClient(self.sdk_key, self.options)

        event = Event(
            type="user",
            target="test_target",
            date=time.time(),
            value=42,
            metaData={"key": "value"},
        )

        with self.assertRaises(ValueError):
            self.client.track(None, event)

        with self.assertRaises(ValueError):
            self.client.track(self.test_user_empty_id, event)

    @responses.activate
    def test_track_bad_event(self):
        self.client = DevCycleLocalClient(self.sdk_key, self.options)

        with self.assertRaises(ValueError):
            self.client.track(self.test_user, None)

        event = Event(
            type=None,
            target="test_target",
            date=time.time(),
            value=42,
            metaData={"key": "value"},
        )
        with self.assertRaises(ValueError):
            self.client.track(self.test_user, event)

        event = Event(
            type="",
            target="test_target",
            date=time.time(),
            value=42,
            metaData={"key": "value"},
        )
        with self.assertRaises(ValueError):
            self.client.track(self.test_user, event)

    @responses.activate
    def test_set_client_custom_data(self):
        self.client = DevCycleLocalClient(self.sdk_key, self.options)
        while not self.client.is_initialized():
            time.sleep(0.1)

        # set the data without error
        client_custom_data = {
            "strProp": "strVal",
            "intProp": 1,
            "floatProp": 1.1,
            "boolProp": True,
            "nullProp": None,
        }
        self.client.set_client_custom_data(client_custom_data)


if __name__ == "__main__":
    unittest.main()
