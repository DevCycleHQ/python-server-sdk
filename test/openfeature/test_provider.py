import logging
import unittest
from unittest.mock import MagicMock

from openfeature.provider.provider import EvaluationContext
from openfeature.flag_evaluation import Reason
from openfeature.exception import (
    ErrorCode,
    TargetingKeyMissingError,
    InvalidContextError,
)

from devcycle_python_sdk.models.variable import Variable, TypeEnum

from devcycle_python_sdk.openfeature.provider import (
    _set_custom_value,
    _create_user_from_context,
    DevCycleProvider,
)


logger = logging.getLogger(__name__)


class DevCycleProviderTest(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.client.is_initialized.return_value = True
        self.provider = DevCycleProvider(self.client)

    def test_resolve_details_client_not_ready(self):
        self.client.is_initialized.return_value = False

        details = self.provider._resolve(
            "test-flag", False, EvaluationContext("test-user")
        )

        self.assertIsNotNone(details)
        self.assertEqual(details.value, False)
        self.assertEqual(details.reason, Reason.ERROR)
        self.assertEqual(details.error_code, ErrorCode.PROVIDER_NOT_READY)

    def test_resolve_details_client_no_user_in_context(self):
        context = EvaluationContext(targeting_key=None, attributes={})

        with self.assertRaises(TargetingKeyMissingError):
            self.provider._resolve("test-flag", False, context)

    def test_resolve_details_no_key(self):
        self.client.variable.side_effect = ValueError("test error")
        context = EvaluationContext(targeting_key="user-1234")
        with self.assertRaises(InvalidContextError):
            self.provider._resolve(None, False, context)

    def test_resolve_details_no_default_value(self):
        self.client.variable.side_effect = ValueError("test error")
        context = EvaluationContext(targeting_key="user-1234")
        with self.assertRaises(InvalidContextError):
            self.provider._resolve("test-flag", None, context)

    def test_resolve_details_client_returns_none(self):
        self.client.variable.return_value = None
        context = EvaluationContext(targeting_key="user-1234")

        details = self.provider._resolve("test-flag", False, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, False)
        self.assertEqual(details.reason, Reason.DEFAULT)

    def test_resolve_details_client_returns_default_variable(self):
        self.client.variable.return_value = Variable.create_default_variable(
            key="test-flag", default_value=False
        )
        context = EvaluationContext(targeting_key="user-1234")
        details = self.provider._resolve("test-flag", False, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, False)
        self.assertEqual(details.reason, Reason.DEFAULT)

    def test_resolve_details_client_returns_targeted_variable(self):
        self.client.variable.return_value = Variable(
            _id=None,
            value=True,
            key="test-flag",
            type=TypeEnum.BOOLEAN,
            isDefaulted=False,
            defaultValue=False,
        )

        context = EvaluationContext(targeting_key="user-1234")
        details = self.provider._resolve("test-flag", False, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, True)
        self.assertEqual(details.reason, Reason.TARGETING_MATCH)


class UserDataFromContextTest(unittest.TestCase):
    def test_create_user_from_context_no_context(self):
        with self.assertRaises(TargetingKeyMissingError):
            _create_user_from_context(None)

    def test_create_user_from_context_no_user_id(self):
        with self.assertRaises(TargetingKeyMissingError):
            _create_user_from_context(
                EvaluationContext(targeting_key=None, attributes={})
            )

        with self.assertRaises(TargetingKeyMissingError):
            _create_user_from_context(
                EvaluationContext(targeting_key=None, attributes=None)
            )

        with self.assertRaises(TargetingKeyMissingError):
            _create_user_from_context(
                EvaluationContext(targeting_key=None, attributes={"user_id": None})
            )

    def test_create_user_from_context_only_user_id(self):
        test_user_id = "12345"
        context = EvaluationContext(targeting_key=test_user_id, attributes=None)
        user = _create_user_from_context(context)
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, test_user_id)

        context = EvaluationContext(
            targeting_key=None, attributes={"user_id": test_user_id}
        )
        user = _create_user_from_context(context)
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, test_user_id)

        # ensure that targeting_key takes precedence over user_id
        context = EvaluationContext(
            targeting_key=test_user_id, attributes={"user_id": "99999"}
        )
        user = _create_user_from_context(context)
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, test_user_id)

    def test_create_user_from_context_with_attributes(self):
        test_user_id = "12345"
        context = EvaluationContext(
            targeting_key=test_user_id,
            attributes={
                "user_id": "1234",
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

    def test_create_user_from_context_with_unknown_data_fields(self):
        test_user_id = "12345"
        context = EvaluationContext(
            targeting_key=test_user_id,
            attributes={
                "strValue": "hello",
                "intValue": 123,
                "floatValue": 3.1456,
                "boolValue": True,
            },
        )
        user = _create_user_from_context(context)
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, test_user_id)

        # the fields should get reassigned to custom_data
        self.assertEqual(
            user.customData,
            {
                "strValue": "hello",
                "intValue": 123,
                "floatValue": 3.1456,
                "boolValue": True,
            },
        )
        self.assertEqual(user.privateCustomData, None)

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
