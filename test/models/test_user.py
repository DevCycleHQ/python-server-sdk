import logging
import unittest

from devcycle_python_sdk.models.user import DevCycleUser

from openfeature.provider import EvaluationContext
from openfeature.exception import TargetingKeyMissingError, InvalidContextError


logger = logging.getLogger(__name__)


class DevCycleUserTest(unittest.TestCase):
    def test_create_user_from_context_no_context(self):
        with self.assertRaises(TargetingKeyMissingError):
            DevCycleUser.create_user_from_context(None)

    def test_create_user_from_context_no_user_id(self):
        with self.assertRaises(TargetingKeyMissingError):
            DevCycleUser.create_user_from_context(
                EvaluationContext(targeting_key=None, attributes={})
            )

        with self.assertRaises(TargetingKeyMissingError):
            DevCycleUser.create_user_from_context(
                EvaluationContext(targeting_key=None, attributes=None)
            )

        with self.assertRaises(TargetingKeyMissingError):
            DevCycleUser.create_user_from_context(
                EvaluationContext(targeting_key=None, attributes={"user_id": None})
            )

    def test_create_user_from_context_only_user_id(self):
        test_user_id = "12345"
        context = EvaluationContext(targeting_key=test_user_id, attributes=None)
        user = DevCycleUser.create_user_from_context(context)
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, test_user_id)

        context = EvaluationContext(
            targeting_key=None, attributes={"user_id": test_user_id}
        )
        user = DevCycleUser.create_user_from_context(context)
        self.assertIsNotNone(user)
        self.assertEqual(user.user_id, test_user_id)

        # ensure that targeting_key takes precedence over user_id
        context = EvaluationContext(
            targeting_key=test_user_id, attributes={"user_id": "99999"}
        )
        user = DevCycleUser.create_user_from_context(context)
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
        user = DevCycleUser.create_user_from_context(context)
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
        user = DevCycleUser.create_user_from_context(context)
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
        user = DevCycleUser.create_user_from_context(context)
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
        with self.assertRaises(InvalidContextError):
            DevCycleUser._set_custom_value(custom_data, None, None)

        custom_data = {}
        DevCycleUser._set_custom_value(custom_data, "key1", None)
        self.assertDictEqual(custom_data, {"key1": None})

        custom_data = {}
        DevCycleUser._set_custom_value(custom_data, "key1", "value1")
        self.assertDictEqual(custom_data, {"key1": "value1"})

        custom_data = {}
        DevCycleUser._set_custom_value(custom_data, "key1", 1)
        self.assertDictEqual(custom_data, {"key1": 1})

        custom_data = {}
        DevCycleUser._set_custom_value(custom_data, "key1", 3.1456)
        self.assertDictEqual(custom_data, {"key1": 3.1456})

        custom_data = {}
        DevCycleUser._set_custom_value(custom_data, "key1", True)
        self.assertDictEqual(custom_data, {"key1": True})

        custom_data = {}
        with self.assertRaises(InvalidContextError):
            DevCycleUser._set_custom_value(custom_data, "map_data", {"hello": "world"})

        custom_data = {}
        with self.assertRaises(InvalidContextError):
            DevCycleUser._set_custom_value(
                custom_data, "list_data", ["one", "two", "three"]
            )


if __name__ == "__main__":
    unittest.main()
