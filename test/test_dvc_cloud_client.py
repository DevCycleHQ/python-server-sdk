import logging
import unittest
import uuid
from unittest.mock import patch

from devcycle_python_sdk import DVCCloudClient, Variable
from devcycle_python_sdk.dvc_options import DVCCloudOptions
from devcycle_python_sdk.models.user_data import UserData

logger = logging.getLogger(__name__)


class DVCCloudClientTest(unittest.TestCase):
    def setUp(self) -> None:
        sdk_key = "dvc_server_" + str(uuid.uuid4())
        options = DVCCloudOptions()
        self.test_client = DVCCloudClient(sdk_key, options)
        self.test_user = UserData(user_id="test_user_id")
        self.test_user_no_id = UserData(user_id=None)
        self.test_user_empty_id = UserData(user_id="")

    def tearDown(self) -> None:
        pass

    def test_create_client_invalid_sdk_key(self):
        with self.assertRaises(ValueError):
            DVCCloudClient(None, None)

        with self.assertRaises(ValueError):
            DVCCloudClient("", None)

        with self.assertRaises(ValueError):
            DVCCloudClient("no prefix in key", None)

    def test_create_client_diff_sdk_keys(self):
        # ensure no exception is generated
        client = DVCCloudClient("dvc_server_" + str(uuid.uuid4()), None)
        self.assertIsNotNone(client)
        client = DVCCloudClient("server_" + str(uuid.uuid4()), None)
        self.assertIsNotNone(client)

    def test_create_client_no_options(self):
        sdk_key = "dvc_server_" + str(uuid.uuid4())
        empty_options = DVCCloudOptions()
        client = DVCCloudClient(sdk_key, empty_options)
        self.assertIsNotNone(client)

        option_with_data = DVCCloudOptions(enable_edge_db=False,
                                           bucketing_api_uri="https://localhost:8080",
                                           config_cdn_uri="https://localhost:8080",
                                           events_api_uri="https://localhost:8080")
        client = DVCCloudClient(sdk_key, option_with_data)
        self.assertIsNotNone(client)

    def test_variable_value_bad_user(self):
        with self.assertRaises(ValueError):
            self.test_client.variable_value(None, "strKey", "default_value")

        with self.assertRaises(ValueError):
            self.test_client.variable_value(self.test_user_no_id, "strKey", "default_value")

        with self.assertRaises(ValueError):
            self.test_client.variable_value(self.test_user_empty_id, "strKey", "default_value")

    @patch('devcycle_python_sdk.BucketingAPIClient.variable')
    def test_variable_value_defaults(self, mock_variable_value_call):
        mock_variable_value_call.return_value = Variable.create_default_variable("strKey", "default_value")
        result = self.test_client.variable_value(self.test_user, "strKey", "default_value")
        self.assertEqual(result, "default_value")

        mock_variable_value_call.return_value = Variable.create_default_variable("numKey", 42)
        mock_variable_value_call.return_value = Variable.create_default_variable("numKey", 42)
        mock_variable_value_call.return_value = Variable.create_default_variable("numKey", 42)
        result = self.test_client.variable_value(self.test_user, "numKey", 42)
        self.assertEqual(result, 42)

        mock_variable_value_call.return_value = Variable.create_default_variable("boolKey", True)
        result = self.test_client.variable_value(self.test_user, "boolKey", True)
        self.assertEqual(result, True)

        mock_variable_value_call.return_value = Variable.create_default_variable("jsonKey", {"prop1": "value"})
        result = self.test_client.variable_value(self.test_user, "jsonKey", {"prop1": "value"})
        self.assertDictEqual(result, {"prop1": "value"})

        mock_variable_value_call.reset_mock()
        mock_variable_value_call.side_effect = Exception("Fake HTTP Error")
        result = self.test_client.variable_value(self.test_user, "strKey", "default_value")
        self.assertEqual(result, "default_value")


if __name__ == '__main__':
    unittest.main()
