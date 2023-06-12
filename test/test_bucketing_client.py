import logging
import responses
import unittest
import uuid

from devcycle_python_sdk import DVCCloudOptions
from devcycle_python_sdk.api.bucketing_client import BucketingAPIClient
from devcycle_python_sdk.models.variable import Variable
from devcycle_python_sdk.models.user_data import UserData

logger = logging.getLogger(__name__)


class BucketingClientTest(unittest.TestCase):
    def setUp(self) -> None:
        sdk_key = "dvc_server_" + str(uuid.uuid4())
        options = DVCCloudOptions()
        self.test_client = BucketingAPIClient(sdk_key, options)
        self.test_user = UserData(user_id="test_user_id")

    @responses.activate
    def test_delete_me(self):
        pass

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


if __name__ == "__main__":
    unittest.main()
