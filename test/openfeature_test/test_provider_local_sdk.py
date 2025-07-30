import logging
import time
import unittest

import responses

from devcycle_python_sdk import DevCycleLocalClient, DevCycleLocalOptions
from test.fixture.data import small_config_json

from openfeature.provider import EvaluationContext
from openfeature.flag_evaluation import Reason

logger = logging.getLogger(__name__)


class DevCycleProviderWithLocalSDKTest(unittest.TestCase):
    """
    Tests the DevCycleProvider with actual data from the Local SDK client to confirm data translations work
    """

    def setUp(self) -> None:
        self.sdk_key = "dvc_server_949e4962-c624-4d20-a1ea-7f2501b2ba79"
        self.test_config_json = small_config_json()
        self.test_etag = "2f71454e-3279-4ca7-a8e7-802ce97bef43"

        config_url = "http://localhost/config/v2/server/" + self.sdk_key + ".json"

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
        self.client = None

    def tearDown(self) -> None:
        if self.client:
            self.client.close()
        responses.reset()

    def setup_client(self):
        self.client = DevCycleLocalClient(self.sdk_key, self.options)
        while not self.client.is_initialized():
            time.sleep(0.05)

    @responses.activate
    def test_resolve_boolean_details(self):
        self.setup_client()
        provider = self.client.get_openfeature_provider()

        key = "a-cool-new-feature"
        expected_value = True
        default_value = False

        context = EvaluationContext(targeting_key="1234")
        details = provider.resolve_boolean_details(key, default_value, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, expected_value)
        self.assertEqual(details.reason, Reason.TARGETING_MATCH)
        self.assertIsNotNone(details.flag_metadata)
        self.assertEqual(details.flag_metadata["evalReasonDetails"], "All Users")
        self.assertEqual(
            details.flag_metadata["evalReasonTargetId"], "63125321d31c601f992288bc"
        )

    @responses.activate
    def test_resolve_integer_details(self):
        self.setup_client()
        provider = self.client.get_openfeature_provider()

        key = "num-var"
        expected_value = 12345
        default_value = 0

        context = EvaluationContext(targeting_key="1234")
        details = provider.resolve_integer_details(key, default_value, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, expected_value)
        self.assertEqual(details.reason, Reason.TARGETING_MATCH)
        self.assertIsNotNone(details.flag_metadata)
        self.assertEqual(details.flag_metadata["evalReasonDetails"], "All Users")
        self.assertEqual(
            details.flag_metadata["evalReasonTargetId"], "63125321d31c601f992288bc"
        )

    @responses.activate
    def test_resolve_float_details(self):
        self.setup_client()
        provider = self.client.get_openfeature_provider()

        key = "float-var"
        expected_value = 3.14159
        default_value = 0.0001

        context = EvaluationContext(targeting_key="1234")
        details = provider.resolve_float_details(key, default_value, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, expected_value)
        self.assertEqual(details.reason, Reason.TARGETING_MATCH)
        self.assertIsNotNone(details.flag_metadata)
        self.assertEqual(details.flag_metadata["evalReasonDetails"], "All Users")
        self.assertEqual(
            details.flag_metadata["evalReasonTargetId"], "63125321d31c601f992288bc"
        )

    @responses.activate
    def test_resolve_string_details(self):
        self.setup_client()
        provider = self.client.get_openfeature_provider()

        key = "string-var"
        expected_value = "variationOn"
        default_value = "default_value"

        context = EvaluationContext(targeting_key="1234")
        details = provider.resolve_string_details(key, default_value, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, expected_value)
        self.assertEqual(details.reason, Reason.TARGETING_MATCH)
        self.assertIsNotNone(details.flag_metadata)
        self.assertEqual(details.flag_metadata["evalReasonDetails"], "All Users")
        self.assertEqual(
            details.flag_metadata["evalReasonTargetId"], "63125321d31c601f992288bc"
        )

    @responses.activate
    def test_resolve_object_details(self):
        self.setup_client()
        provider = self.client.get_openfeature_provider()

        key = "json-var"
        expected_value = {
            "displayText": "This variation is on",
            "showDialog": True,
            "maxUsers": 100,
        }
        default_value = {"default": "value"}

        context = EvaluationContext(targeting_key="1234")
        details = provider.resolve_string_details(key, default_value, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, expected_value)
        self.assertEqual(details.reason, Reason.TARGETING_MATCH)
        self.assertIsNotNone(details.flag_metadata)
        self.assertEqual(details.flag_metadata["evalReasonDetails"], "All Users")
        self.assertEqual(
            details.flag_metadata["evalReasonTargetId"], "63125321d31c601f992288bc"
        )
