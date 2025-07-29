import logging
import unittest
import uuid

from time import time
from unittest.mock import patch


from devcycle_python_sdk import DevCycleCloudClient, DevCycleCloudOptions
from devcycle_python_sdk.models.eval_hook import EvalHook
from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.variable import Variable, TypeEnum
from devcycle_python_sdk.models.event import DevCycleEvent
from devcycle_python_sdk.exceptions import (
    CloudClientUnauthorizedError,
    NotFoundError,
)

logger = logging.getLogger(__name__)


class DevCycleCloudClientTest(unittest.TestCase):
    def setUp(self) -> None:
        sdk_key = "dvc_server_" + str(uuid.uuid4())
        options = DevCycleCloudOptions()
        self.test_client = DevCycleCloudClient(sdk_key, options)
        self.test_user = DevCycleUser(user_id="test_user_id")
        self.test_user_no_id = DevCycleUser(user_id=None)  # type: ignore
        self.test_user_empty_id = DevCycleUser(user_id="")

    def tearDown(self) -> None:
        self.test_client.clear_hooks()
        pass

    def test_create_client_invalid_sdk_key(self):
        with self.assertRaises(ValueError):
            DevCycleCloudClient(None, None)

        with self.assertRaises(ValueError):
            DevCycleCloudClient("", None)

        with self.assertRaises(ValueError):
            DevCycleCloudClient("no prefix in key", None)

    def test_create_client_diff_sdk_keys(self):
        # ensure no exception is generated
        client = DevCycleCloudClient("dvc_server_" + str(uuid.uuid4()), None)
        self.assertIsNotNone(client)
        client = DevCycleCloudClient("server_" + str(uuid.uuid4()), None)
        self.assertIsNotNone(client)

    def test_create_client_no_options(self):
        sdk_key = "dvc_server_" + str(uuid.uuid4())
        empty_options = DevCycleCloudOptions()
        client = DevCycleCloudClient(sdk_key, empty_options)
        self.assertIsNotNone(client)

        option_with_data = DevCycleCloudOptions(
            enable_edge_db=False,
            bucketing_api_uri="https://localhost:8080",
        )
        client = DevCycleCloudClient(sdk_key, option_with_data)
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

    @patch("devcycle_python_sdk.api.bucketing_client.BucketingAPIClient.variable")
    def test_variable_exceptions(self, mock_variable_call):
        # unauthorized - return error
        mock_variable_call.side_effect = CloudClientUnauthorizedError("No auth")
        with self.assertRaises(CloudClientUnauthorizedError):
            self.test_client.variable(self.test_user, "strKey", "default_value")

        # not found - return default
        mock_variable_call.reset_mock()
        mock_variable_call.side_effect = NotFoundError("No auth")
        result = self.test_client.variable(self.test_user, "strKey", "default_value")
        self.assertIsNotNone(result)
        self.assertEqual(result.value, "default_value")
        self.assertTrue(result.isDefaulted)
        self.assertEqual(result.eval.reason, "DEFAULT")
        self.assertEqual(result.eval.details, "Missing Variable")

        # other exception - return default
        mock_variable_call.reset_mock()
        mock_variable_call.side_effect = Exception("failed request")
        result = self.test_client.variable(self.test_user, "strKey", "default_value")
        self.assertIsNotNone(result)
        self.assertEqual(result.value, "default_value")
        self.assertTrue(result.isDefaulted)
        self.assertEqual(result.eval.reason, "DEFAULT")
        self.assertEqual(result.eval.details, "Error")

    @patch("devcycle_python_sdk.api.bucketing_client.BucketingAPIClient.variable")
    def test_variable_type_mismatch(self, mock_variable_call):
        mock_variable_call.return_value = Variable(
            _id="123", key="strKey", value=999, type=TypeEnum.NUMBER
        )

        result = self.test_client.variable(self.test_user, "strKey", "default_value")
        self.assertIsNotNone(result)
        self.assertEqual(result.value, "default_value")
        self.assertTrue(result.isDefaulted)
        self.assertEqual(result.eval.reason, "DEFAULT")
        self.assertEqual(result.eval.details, "Variable Type Mismatch")

    @patch("devcycle_python_sdk.api.bucketing_client.BucketingAPIClient.variable")
    def test_variable_value_defaults(self, mock_variable_call):
        mock_variable_call.return_value = Variable.create_default_variable(
            "strKey", "default_value"
        )
        result = self.test_client.variable(self.test_user, "strKey", "default_value")
        self.assertEqual(result.value, "default_value")
        self.assertTrue(result.isDefaulted)

        mock_variable_call.return_value = Variable.create_default_variable("numKey", 42)
        result = self.test_client.variable(self.test_user, "numKey", 42)
        self.assertEqual(result.value, 42)
        self.assertTrue(result.isDefaulted)

        mock_variable_call.return_value = Variable.create_default_variable(
            "boolKey", True
        )
        result = self.test_client.variable(self.test_user, "boolKey", True)
        self.assertEqual(result.value, True)
        self.assertTrue(result.isDefaulted)

        mock_variable_call.return_value = Variable.create_default_variable(
            "jsonKey", {"prop1": "value"}
        )
        result = self.test_client.variable(
            self.test_user, "jsonKey", {"prop1": "value"}
        )
        self.assertDictEqual(result.value, {"prop1": "value"})
        self.assertTrue(result.isDefaulted)

        mock_variable_call.reset_mock()
        mock_variable_call.side_effect = Exception("Fake HTTP Error")
        result = self.test_client.variable(self.test_user, "strKey", "default_value")
        self.assertEqual(result.value, "default_value")
        self.assertTrue(result.isDefaulted)

    @patch("devcycle_python_sdk.api.bucketing_client.BucketingAPIClient.variables")
    def test_all_variables_bad_user(self, mock_variables_call):
        with self.assertRaises(ValueError):
            self.test_client.all_variables(None)
        mock_variables_call.assert_not_called()

        with self.assertRaises(ValueError):
            self.test_client.all_variables(self.test_user_no_id)
        mock_variables_call.assert_not_called()

        with self.assertRaises(ValueError):
            self.test_client.all_variables(self.test_user_empty_id)
        mock_variables_call.assert_not_called()

    @patch("devcycle_python_sdk.api.bucketing_client.BucketingAPIClient.variables")
    def test_all_variables_exceptions(self, mock_variables_call):
        # unauthorized - return error
        mock_variables_call.side_effect = CloudClientUnauthorizedError("No auth")
        with self.assertRaises(CloudClientUnauthorizedError):
            self.test_client.all_variables(self.test_user)

        # error - return empty
        mock_variables_call.reset_mock()
        mock_variables_call.side_effect = Exception("Some error")
        mock_variables_call.return_value = {}
        result = self.test_client.all_variables(self.test_user)
        self.assertDictEqual(result, {})

    @patch("devcycle_python_sdk.api.bucketing_client.BucketingAPIClient.features")
    def test_all_features_bad_user(self, mock_features_call):
        with self.assertRaises(ValueError):
            self.test_client.all_features(None)
        mock_features_call.assert_not_called()

        with self.assertRaises(ValueError):
            self.test_client.all_features(self.test_user_no_id)
        mock_features_call.assert_not_called()

        with self.assertRaises(ValueError):
            self.test_client.all_features(self.test_user_empty_id)
        mock_features_call.assert_not_called()

    @patch("devcycle_python_sdk.api.bucketing_client.BucketingAPIClient.features")
    def test_all_features_exceptions(self, mock_features_call):
        # unauthorized - return error
        mock_features_call.side_effect = CloudClientUnauthorizedError("No auth")
        with self.assertRaises(CloudClientUnauthorizedError):
            self.test_client.all_features(self.test_user)

        # error - return empty
        mock_features_call.reset_mock()
        mock_features_call.side_effect = Exception("Some error")
        result = self.test_client.all_features(self.test_user)
        self.assertDictEqual(result, {})

    @patch("devcycle_python_sdk.api.bucketing_client.BucketingAPIClient.track")
    def test_track_event_bad_user(self, mock_track_call):
        event = DevCycleEvent(
            type="user",
            target="test_target",
            date=time(),
            value=42,
            metaData={"key": "value"},
        )

        with self.assertRaises(ValueError):
            self.test_client.track(None, event)
        mock_track_call.assert_not_called()

        with self.assertRaises(ValueError):
            self.test_client.track(self.test_user_no_id, event)
        mock_track_call.assert_not_called()

        with self.assertRaises(ValueError):
            self.test_client.track(self.test_user_empty_id, event)
        mock_track_call.assert_not_called()

    @patch("devcycle_python_sdk.api.bucketing_client.BucketingAPIClient.track")
    def test_track_bad_event(self, mock_track_call):
        with self.assertRaises(ValueError):
            self.test_client.track(self.test_user, None)
        mock_track_call.assert_not_called()

        event = DevCycleEvent(
            type=None,
            target="test_target",
            value=42,
            metaData={"key": "value"},
        )
        with self.assertRaises(ValueError):
            self.test_client.track(self.test_user, event)
        mock_track_call.assert_not_called()

        event = DevCycleEvent(
            type="",
            target="test_target",
            value=42,
            metaData={"key": "value"},
        )
        with self.assertRaises(ValueError):
            self.test_client.track(self.test_user, event)
        mock_track_call.assert_not_called()

    @patch("devcycle_python_sdk.api.bucketing_client.BucketingAPIClient.track")
    def test_track_exceptions(self, mock_track_call):
        # unauthorized - return error
        mock_track_call.side_effect = CloudClientUnauthorizedError("No auth")
        with self.assertRaises(CloudClientUnauthorizedError):
            self.test_client.track(
                self.test_user,
                DevCycleEvent(
                    type="user",
                    target="test_target",
                    value=42,
                    metaData={"key": "value"},
                ),
            )

        # other error - shouldn't propagate
        mock_track_call.side_effect = Exception("Some error")
        self.test_client.track(
            self.test_user,
            DevCycleEvent(
                type="user",
                target="test_target",
                value=42,
                metaData={"key": "value"},
            ),
        )

    @patch("devcycle_python_sdk.api.bucketing_client.BucketingAPIClient.variable")
    def test_hooks(self, mock_variable_call):
        mock_variable_call.return_value = Variable(
            _id="123", key="strKey", value=999, type=TypeEnum.NUMBER
        )
        # Test adding hooks
        hook_called = {
            "before": False,
            "after": False,
            "finally": False,
            "error": False,
        }

        def before_hook(context):
            hook_called["before"] = True
            return context

        def after_hook(context, variable):
            hook_called["after"] = True

        def finally_hook(context, variable):
            hook_called["finally"] = True

        def error_hook(context, error):
            hook_called["error"] = True

        self.test_client.add_hook(
            EvalHook(before_hook, after_hook, finally_hook, error_hook)
        )

        # Test hooks called during variable evaluation
        variable = self.test_client.variable(self.test_user, "strKey", 42)
        self.assertTrue(variable.value == 999)
        self.assertFalse(variable.isDefaulted)

        self.assertTrue(hook_called["before"])
        self.assertTrue(hook_called["after"])
        self.assertTrue(hook_called["finally"])
        self.assertFalse(hook_called["error"])

    @patch("devcycle_python_sdk.api.bucketing_client.BucketingAPIClient.variable")
    def test_hook_exceptions(self, mock_variable_call):
        mock_variable_call.return_value = Variable(
            _id="123", key="strKey", value=999, type=TypeEnum.NUMBER
        )
        # Test adding hooks
        hook_called = {
            "before": False,
            "after": False,
            "finally": False,
            "error": False,
        }

        def before_hook(context):
            hook_called["before"] = True
            raise Exception("Before hook failed")

        def after_hook(context, variable):
            hook_called["after"] = True

        def finally_hook(context, variable):
            hook_called["finally"] = True

        def error_hook(context, error):
            hook_called["error"] = True

        self.test_client.add_hook(
            EvalHook(before_hook, after_hook, finally_hook, error_hook)
        )

        # Test hooks called during variable evaluation
        variable = self.test_client.variable(self.test_user, "strKey", 42)
        self.assertTrue(variable.value == 999)
        self.assertFalse(variable.isDefaulted)

        self.assertTrue(hook_called["before"])
        self.assertFalse(hook_called["after"])
        self.assertTrue(hook_called["finally"])
        self.assertTrue(hook_called["error"])


if __name__ == "__main__":
    unittest.main()
