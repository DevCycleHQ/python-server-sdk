import logging
import unittest
from unittest.mock import MagicMock

from openfeature.provider import EvaluationContext
from openfeature.flag_evaluation import Reason
from openfeature.exception import (
    ErrorCode,
    TargetingKeyMissingError,
    InvalidContextError,
    TypeMismatchError,
)

from devcycle_python_sdk.models.variable import Variable, TypeEnum
from devcycle_python_sdk.models.eval_reason import (
    EvalReason,
    DefaultReasonDetails,
)

from devcycle_python_sdk.open_feature_provider.provider import (
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
            key="test-flag",
            default_value=False,
            default_reason_detail=DefaultReasonDetails.USER_NOT_TARGETED,
        )
        context = EvaluationContext(targeting_key="user-1234")
        details = self.provider._resolve("test-flag", False, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, False)
        self.assertEqual(details.reason, Reason.DEFAULT)
        self.assertEqual(
            details.flag_metadata["evalReasonDetails"], "User Not Targeted"
        )

    def test_resolve_boolean_details(self):
        key = "test-flag"
        variable_value = True
        default_value = False

        self.client.variable.return_value = Variable(
            _id=None,
            value=variable_value,
            key=key,
            type=TypeEnum.BOOLEAN,
            isDefaulted=False,
            defaultValue=False,
            eval=EvalReason(
                reason="TARGETING_MATCH", details="All Users", target_id="targetId"
            ),
        )

        context = EvaluationContext(targeting_key="user-1234")
        details = self.provider.resolve_boolean_details(key, default_value, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, variable_value)
        self.assertEqual(details.reason, Reason.TARGETING_MATCH)
        self.assertEqual(details.reason, Reason.TARGETING_MATCH)
        self.assertEqual(details.flag_metadata["evalReasonDetails"], "All Users")
        self.assertEqual(details.flag_metadata["evalReasonTargetId"], "targetId")

    def test_resolve_string_details(self):
        key = "test-flag"
        variable_value = "some string"
        default_value = "default string"

        self.client.variable.return_value = Variable(
            _id=None,
            value=variable_value,
            key=key,
            type=TypeEnum.STRING,
            isDefaulted=False,
            defaultValue=False,
            eval=EvalReason(
                reason="TARGETING_MATCH", details="All Users", target_id="targetId"
            ),
        )

        context = EvaluationContext(targeting_key="user-1234")
        details = self.provider.resolve_string_details(key, default_value, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, variable_value)
        self.assertIsInstance(details.value, str)
        self.assertEqual(details.reason, Reason.TARGETING_MATCH)
        self.assertEqual(details.flag_metadata["evalReasonDetails"], "All Users")
        self.assertEqual(details.flag_metadata["evalReasonTargetId"], "targetId")

    def test_resolve_integer_details(self):
        key = "test-flag"
        variable_value = 12345
        default_value = 0

        self.client.variable.return_value = Variable(
            _id=None,
            value=variable_value,
            key=key,
            type=TypeEnum.STRING,
            isDefaulted=False,
            defaultValue=False,
            eval=EvalReason(
                reason="TARGETING_MATCH", details="All Users", target_id="targetId"
            ),
        )

        context = EvaluationContext(targeting_key="user-1234")
        details = self.provider.resolve_integer_details(key, default_value, context)

        self.assertIsNotNone(details)
        self.assertIsInstance(details.value, int)
        self.assertEqual(details.value, variable_value)
        self.assertEqual(details.reason, Reason.TARGETING_MATCH)
        self.assertEqual(details.flag_metadata["evalReasonDetails"], "All Users")
        self.assertEqual(details.flag_metadata["evalReasonTargetId"], "targetId")

    def test_resolve_float_details(self):
        key = "test-flag"
        variable_value = 3.145
        default_value = 0.0

        self.client.variable.return_value = Variable(
            _id=None,
            value=variable_value,
            key=key,
            type=TypeEnum.STRING,
            isDefaulted=False,
            defaultValue=False,
            eval=EvalReason(reason="SPLIT", details="Rollout", target_id="targetId"),
        )

        context = EvaluationContext(targeting_key="user-1234")
        details = self.provider.resolve_float_details(key, default_value, context)

        self.assertIsNotNone(details)
        self.assertIsInstance(details.value, float)
        self.assertEqual(details.value, variable_value)
        self.assertEqual(details.reason, Reason.SPLIT)
        self.assertEqual(details.flag_metadata["evalReasonDetails"], "Rollout")
        self.assertEqual(details.flag_metadata["evalReasonTargetId"], "targetId")

    def test_resolve_object_details_verify_default_value(self):
        key = "test-flag"
        context = EvaluationContext(targeting_key="user-1234")

        # Only flat dictionaries are supported as objects
        # lists, primitives and nested objects are not supported
        with self.assertRaises(TypeMismatchError):
            self.provider.resolve_object_details(key, [], context)

        with self.assertRaises(TypeMismatchError):
            self.provider.resolve_object_details(key, 1234, context)

        with self.assertRaises(TypeMismatchError):
            self.provider.resolve_object_details(key, 3.14, context)

        with self.assertRaises(TypeMismatchError):
            self.provider.resolve_object_details(key, False, context)

        with self.assertRaises(TypeMismatchError):
            self.provider.resolve_object_details(key, "some string", context)

        # test dictionaries with nested objects
        with self.assertRaises(TypeMismatchError):
            self.provider.resolve_object_details(
                key, {"nestedMap": {"someProp": "some value"}}, context
            )

    def test_resolve_object_details(self):
        key = "test-flag"
        variable_value = {"some": "value"}
        default_value = {}

        self.client.variable.return_value = Variable(
            _id=None,
            value=variable_value,
            key=key,
            type=TypeEnum.STRING,
            isDefaulted=False,
            defaultValue=False,
            eval=EvalReason(
                reason="TARGETING_MATCH", details="Rollout", target_id="targetId"
            ),
        )

        context = EvaluationContext(targeting_key="user-1234")
        details = self.provider.resolve_object_details(key, default_value, context)

        self.assertIsNotNone(details)
        self.assertIsInstance(details.value, dict)
        self.assertDictEqual(details.value, variable_value)
        self.assertEqual(details.reason, Reason.TARGETING_MATCH)
        self.assertIsNotNone(details.flag_metadata)
        self.assertEqual(details.flag_metadata["evalReasonDetails"], "Rollout")
        self.assertEqual(details.flag_metadata["evalReasonTargetId"], "targetId")

    def test_resolve_string_details_null_eval(self):
        key = "test-flag"
        variable_value = "some string"
        default_value = "default string"

        self.client.variable.return_value = Variable(
            _id=None,
            value=variable_value,
            key=key,
            type=TypeEnum.STRING,
            isDefaulted=False,
            defaultValue=False,
        )

        context = EvaluationContext(targeting_key="user-1234")
        details = self.provider.resolve_string_details(key, default_value, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, variable_value)
        self.assertIsInstance(details.value, str)
        self.assertEqual(details.reason, Reason.TARGETING_MATCH)

    def test_default_string_details_null_eval(self):
        key = "test-flag"
        default_value = "default string"

        self.client.variable.return_value = Variable(
            _id=None,
            value=default_value,
            key=key,
            type=TypeEnum.STRING,
            isDefaulted=True,
            defaultValue=False,
        )

        context = EvaluationContext(targeting_key="user-1234")
        details = self.provider.resolve_string_details(key, default_value, context)

        self.assertIsNotNone(details)
        self.assertEqual(details.value, default_value)
        self.assertIsInstance(details.value, str)
        self.assertEqual(details.reason, Reason.DEFAULT)


if __name__ == "__main__":
    unittest.main()
