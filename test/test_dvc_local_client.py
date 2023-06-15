import logging
import unittest
import uuid
from time import time
from unittest.mock import patch

from devcycle_python_sdk import DevCycleLocalClient, DevCycleLocalOptions
from devcycle_python_sdk.models.event import Event
from devcycle_python_sdk.models.user import User
from test.fixture_helper import get_small_config_json

logger = logging.getLogger(__name__)


class DVCLocalClientTest(unittest.TestCase):

    @patch("devcycle_python_sdk.api.config_client.ConfigAPIClient.get_config")
    def setUp(self, mock_get_config) -> None:
        self.test_config_json = get_small_config_json()
        self.test_etag = str(uuid.uuid4())
        mock_get_config.return_value = (self.test_config_json, self.test_etag)

        self.sdk_key = "dvc_server_" + str(uuid.uuid4())
        options = DevCycleLocalOptions(config_polling_interval_ms=100)
        self.test_client = DevCycleLocalClient(self.sdk_key, options)

        self.test_user = User(user_id="test_user_id")
        self.test_user_no_id = User(user_id=None)
        self.test_user_empty_id = User(user_id="")

    def tearDown(self) -> None:
        self.test_client.close()

    def test_validate_sdk_key(self):
        with self.assertRaises(ValueError):
            self.test_client._validate_sdk_key(None)

        with self.assertRaises(ValueError):
            self.test_client._validate_sdk_key("")

        with self.assertRaises(ValueError):
            self.test_client._validate_sdk_key("client_" + str(uuid.uuid4()))

        with self.assertRaises(ValueError):
            self.test_client._validate_sdk_key(str(uuid.uuid4()))

    def test_validate_user(self):
        with self.assertRaises(ValueError):
            self.test_client._validate_user(None)

        with self.assertRaises(ValueError):
            self.test_client._validate_user(self.test_user_no_id)

        with self.assertRaises(ValueError):
            self.test_client._validate_user(self.test_user_empty_id)

    def test_create_client_invalid_sdk_key(self):
        with self.assertRaises(ValueError):
            DevCycleLocalClient(None, None)

        with self.assertRaises(ValueError):
            DevCycleLocalClient("", None)

        with self.assertRaises(ValueError):
            DevCycleLocalClient("no prefix in key", None)

    def test_variable_bad_user(self):
        with self.assertRaises(ValueError):
            self.test_client.variable(None, "strKey", "default_value")

        with self.assertRaises(ValueError):
            self.test_client.variable(self.test_user_no_id, "strKey", "default_value")

        with self.assertRaises(ValueError):
            self.test_client.variable(
                self.test_user_empty_id, "strKey", "default_value"
            )

    def test_variable_bad_key_and_value(self):
        with self.assertRaises(ValueError):
            self.test_client.variable(self.test_user, None, "default_value")

        with self.assertRaises(ValueError):
            self.test_client.variable(self.test_user, "", "default_value")

            with self.assertRaises(ValueError):
                self.test_client.variable(self.test_user, "strKey", None)

    def test_all_variables_bad_user(self):
        with self.assertRaises(ValueError):
            self.test_client.all_variables(None)

        with self.assertRaises(ValueError):
            self.test_client.all_variables(self.test_user_no_id)

        with self.assertRaises(ValueError):
            self.test_client.all_variables(self.test_user_empty_id)

    def test_all_features_bad_user(self):
        with self.assertRaises(ValueError):
            self.test_client.all_features(None)

        with self.assertRaises(ValueError):
            self.test_client.all_features(self.test_user_no_id)

        with self.assertRaises(ValueError):
            self.test_client.all_features(self.test_user_empty_id)

    def test_track_event_bad_user(self):
        event = Event(
            type="user",
            target="test_target",
            date=time(),
            value=42,
            metaData={"key": "value"},
        )

        with self.assertRaises(ValueError):
            self.test_client.track(None, event)

        with self.assertRaises(ValueError):
            self.test_client.track(self.test_user_no_id, event)

        with self.assertRaises(ValueError):
            self.test_client.track(self.test_user_empty_id, event)

    def test_track_bad_event(self):
        with self.assertRaises(ValueError):
            self.test_client.track(self.test_user, None)

        event = Event(
            type=None,
            target="test_target",
            date=time(),
            value=42,
            metaData={"key": "value"},
        )
        with self.assertRaises(ValueError):
            self.test_client.track(self.test_user, event)

        event = Event(
            type="",
            target="test_target",
            date=time(),
            value=42,
            metaData={"key": "value"},
        )
        with self.assertRaises(ValueError):
            self.test_client.track(self.test_user, event)


if __name__ == "__main__":
    unittest.main()
