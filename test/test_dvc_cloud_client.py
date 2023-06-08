import logging
import unittest
import uuid

from devcycle_python_sdk import DVCCloudClient, DVCCloudOptions

logger = logging.getLogger(__name__)


class DVCCloudClientTest(unittest.TestCase):
    # def setUp(self) -> None:

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


if __name__ == '__main__':
    unittest.main()
