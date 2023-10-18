import logging
import unittest
from unittest.mock import MagicMock

from openfeature.provider.provider import EvaluationContext
from openfeature.flag_evaluation import Reason
from openfeature.exception import ErrorCode

from devcycle_python_sdk.openfeature.provider import (
    _set_custom_value,
    _create_user_from_context,
    UserDataError,
    DevCycleProvider,
)

logger = logging.getLogger(__name__)


class DevCycleProviderTest(unittest.TestCase):
    def test_resolve_details_client_not_ready(self):
        client = MagicMock()
        client.is_initialized.return_value = False
        provider = DevCycleProvider(client)

        details = provider._resolve_details(
            "test-flag", False, EvaluationContext("test-user")
        )

        self.assertIsNotNone(details)
        self.assertEqual(details.value, False)
        self.assertEqual(details.reason, Reason.ERROR)
        self.assertEqual(details.error_code, ErrorCode.PROVIDER_NOT_READY)

    def test_resolve_details_client_no_user_in_context(self):
        client = MagicMock()
        client.is_initialized.return_value = True
        provider = DevCycleProvider(client)
        context = EvaluationContext(targeting_key=None, attributes={})
        details = provider._resolve_details("test-flag", False, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, False)
        self.assertEqual(details.reason, Reason.ERROR)
        self.assertEqual(details.error_code, ErrorCode.TARGETING_KEY_MISSING)

    def test_resolve_details_client_no_key(self):
        client = MagicMock()
        client.is_initialized.return_value = True
        provider = DevCycleProvider(client)
        context = EvaluationContext(targeting_key=None, attributes={})
        details = provider._resolve_details(None, False, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, False)
        self.assertEqual(details.reason, Reason.ERROR)
        self.assertEqual(details.error_code, ErrorCode.TARGETING_KEY_MISSING)


class UserDataFromContextTest(unittest.TestCase):
    def test_create_user_from_context_no_context(self):
        with self.assertRaises(UserDataError):
            _create_user_from_context(None)

    def test_create_user_from_context_no_user_id(self):
        with self.assertRaises(UserDataError):
            _create_user_from_context(
                EvaluationContext(targeting_key=None, attributes={})
            )

        with self.assertRaises(UserDataError):
            _create_user_from_context(
                EvaluationContext(targeting_key=None, attributes=None)
            )

        with self.assertRaises(UserDataError):
            _create_user_from_context(
                EvaluationContext(targeting_key=None, attributes={"userId": None})
            )

    def test_create_user_from_context_only_user_id(self):
        test_user_id = "12345"
        context = EvaluationContext(targeting_key=test_user_id, attributes=None)
        user = _create_user_from_context(context)
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, test_user_id)

        context = EvaluationContext(
            targeting_key=None, attributes={"userId": test_user_id}
        )
        user = _create_user_from_context(context)
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, test_user_id)

        # ensure that targeting_key takes precedence over userId
        context = EvaluationContext(
            targeting_key=test_user_id, attributes={"userId": "99999"}
        )
        user = _create_user_from_context(context)
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, test_user_id)

    def test_create_user_from_context_with_attributes(self):
        test_user_id = "12345"
        context = EvaluationContext(
            targeting_key=test_user_id,
            attributes={
                "userId": "1234",
                "email": "someone@example.com",
                "name": "John Doe",
                "language": "en",
                "country": "US",
                "appVersion": "1.0.0",
                "appBuild": "1",
                "deviceModel": "iPhone X21",
            },
        )
        user = _create_user_from_context(context)
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, test_user_id)
        self.assertEqual(user.email, context.attributes["email"])
        self.assertEqual(user.name, context.attributes["name"])
        self.assertEqual(user.language, context.attributes["language"])
        self.assertEqual(user.country, context.attributes["country"])
        self.assertEqual(user.appVersion, context.attributes["appVersion"])
        self.assertEqual(user.appBuild, context.attributes["appBuild"])
        self.assertEqual(user.deviceModel, context.attributes["deviceModel"])

    def test_create_user_from_context_with_custom_data(self):
        test_user_id = "12345"
        context = EvaluationContext(
            targeting_key=test_user_id,
            attributes={
                "customData": {
                    "strValue": "hello",
                    "intValue": 123,
                    "floatValue": 3.1456,
                    "boolValue": True,
                },
                "privateCustomData": {
                    "strValue": "world",
                    "intValue": 789,
                    "floatValue": 0.0001,
                    "BoolValue": False,
                },
            },
        )
        user = _create_user_from_context(context)
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, test_user_id)

        self.assertEqual(
            user.customData,
            {
                "strValue": "hello",
                "intValue": 123,
                "floatValue": 3.1456,
                "boolValue": True,
            },
        )
        self.assertEqual(
            user.privateCustomData,
            {
                "strValue": "world",
                "intValue": 789,
                "floatValue": 0.0001,
                "BoolValue": False,
            },
        )

    def test_set_custom_value(self):
        custom_data = {}
        _set_custom_value(custom_data, None, None)
        self.assertDictEqual(custom_data, {})

        custom_data = {}
        _set_custom_value(custom_data, "key1", None)
        self.assertDictEqual(custom_data, {})

        custom_data = {}
        _set_custom_value(custom_data, "key1", "value1")
        self.assertDictEqual(custom_data, {"key1": "value1"})

        custom_data = {}
        _set_custom_value(custom_data, "key1", 1)
        self.assertDictEqual(custom_data, {"key1": 1})

        custom_data = {}
        _set_custom_value(custom_data, "key1", 3.1456)
        self.assertDictEqual(custom_data, {"key1": 3.1456})

        custom_data = {}
        _set_custom_value(custom_data, "key1", True)
        self.assertDictEqual(custom_data, {"key1": True})

        custom_data = {}
        _set_custom_value(custom_data, "map_data", {"hello": "world"})
        self.assertDictEqual(custom_data, {})

        custom_data = {}
        _set_custom_value(custom_data, "list_data", ["one", "two", "three"])
        self.assertDictEqual(custom_data, {})


if __name__ == "__main__":
    unittest.main()
