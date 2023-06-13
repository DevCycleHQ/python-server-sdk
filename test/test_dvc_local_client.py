import logging
import unittest
import uuid
from time import time

from devcycle_python_sdk import DevCycleLocalClient, DevCycleLocalOptions
from devcycle_python_sdk.models.event import Event
from devcycle_python_sdk.models.user import User

logger = logging.getLogger(__name__)


class DVCLocalClientTest(unittest.TestCase):
    def setUp(self) -> None:
        sdk_key = "dvc_server_" + str(uuid.uuid4())
        options = DevCycleLocalOptions()
        self.test_client = DevCycleLocalClient(sdk_key, options)
        self.test_user = User(user_id="test_user_id")
        self.test_user_no_id = User(user_id=None)
        self.test_user_empty_id = User(user_id="")

    def tearDown(self) -> None:
        pass

    def test_create_client_invalid_sdk_key(self):
        with self.assertRaises(ValueError):
            DevCycleLocalClient(None, None)

        with self.assertRaises(ValueError):
            DevCycleLocalClient("", None)

        with self.assertRaises(ValueError):
            DevCycleLocalClient("no prefix in key", None)

    def test_create_client_diff_sdk_keys(self):
        # ensure no exception is generated
        client = DevCycleLocalClient("dvc_server_" + str(uuid.uuid4()), None)
        self.assertIsNotNone(client)
        client = DevCycleLocalClient("server_" + str(uuid.uuid4()), None)
        self.assertIsNotNone(client)

    def test_create_client_no_options(self):
        sdk_key = "dvc_server_" + str(uuid.uuid4())
        empty_options = DevCycleLocalOptions()
        client = DevCycleLocalClient(sdk_key, empty_options)
        self.assertIsNotNone(client)

        option_with_data = DevCycleLocalOptions(
            events_api_uri="https://localhost:8080",
            config_cdn_uri="https://localhost:8080",
            flush_event_queue_size=10000,
            max_event_queue_size=2500
        )
        client = DevCycleLocalClient(sdk_key, option_with_data)
        self.assertIsNotNone(client)

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
