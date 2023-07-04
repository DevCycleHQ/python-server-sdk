import logging

import unittest

from devcycle_python_sdk.models.variable import TypeEnum
from devcycle_python_sdk.models.user import DevCycleUser
import devcycle_python_sdk.protobuf.utils as utils
import devcycle_python_sdk.protobuf.variableForUserParams_pb2 as pb2

logger = logging.getLogger(__name__)


class VersionTest(unittest.TestCase):
    def test_create_nullable_double(self):
        result = utils.create_nullable_double(None)
        self.assertIsNotNone(result)
        self.assertTrue(result.isNull)

        result = utils.create_nullable_double(99.0)
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull)
        self.assertEqual(result.value, 99.0)

    def test_create_nullable_string(self):
        result = utils.create_nullable_string(None)
        self.assertIsNotNone(result)
        self.assertTrue(result.isNull)

        result = utils.create_nullable_string("")
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull)
        self.assertEqual(result.value, "")

        result = utils.create_nullable_string("test value")
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull)
        self.assertEqual(result.value, "test value")

    def test_create_nullable_custom_data(self):
        result = utils.create_nullable_custom_data(None)
        self.assertIsNotNone(result)
        self.assertTrue(result.isNull)

        result = utils.create_nullable_custom_data(dict())
        self.assertIsNotNone(result)
        self.assertTrue(result.isNull)

        result = utils.create_nullable_custom_data({"strProp": "test value"})
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull)
        self.assertEqual(result.value["strProp"].type, pb2.CustomDataType.Str)
        self.assertEqual(result.value["strProp"].stringValue, "test value")

        result = utils.create_nullable_custom_data({"boolProp": False})
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull)
        self.assertEqual(result.value["boolProp"].type, pb2.CustomDataType.Bool)
        self.assertEqual(result.value["boolProp"].boolValue, False)

        result = utils.create_nullable_custom_data({"numProp": 1234.0})
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull)
        self.assertEqual(result.value["numProp"].type, pb2.CustomDataType.Num)
        self.assertEqual(result.value["numProp"].doubleValue, 1234.0)

    def test_create_variable_string(self):
        sdk_var = pb2.SDKVariable_PB(
            _id="test id",
            key="test key",
            stringValue="test value",
            type=pb2.VariableType_PB.String,
        )

        var = utils.create_variable(sdk_var, "default value")
        self.assertIsNotNone(var)
        self.assertEqual(var.type, TypeEnum.STRING)
        self.assertIsNone(var._id)
        self.assertEqual(var.key, sdk_var.key)
        self.assertEqual(var.value, sdk_var.stringValue)
        self.assertEqual(var.defaultValue, "default value")
        self.assertFalse(var.isDefaulted)

    def test_create_variable_boolean(self):
        sdk_var = pb2.SDKVariable_PB(
            _id="test id",
            key="test key",
            boolValue=True,
            type=pb2.VariableType_PB.Boolean,
        )

        var = utils.create_variable(sdk_var, False)
        self.assertIsNotNone(var)
        self.assertEqual(var.type, TypeEnum.BOOLEAN)
        self.assertIsNone(var._id)
        self.assertEqual(var.key, sdk_var.key)
        self.assertEqual(var.value, sdk_var.boolValue)
        self.assertEqual(var.defaultValue, False)
        self.assertFalse(var.isDefaulted)

    def test_create_variable_number(self):
        sdk_var = pb2.SDKVariable_PB(
            _id="test id",
            key="test key",
            doubleValue=99.99,
            type=pb2.VariableType_PB.Number,
        )

        var = utils.create_variable(sdk_var, 0)
        self.assertIsNotNone(var)
        self.assertEqual(var.type, TypeEnum.NUMBER)
        self.assertIsNone(var._id)
        self.assertEqual(var.key, sdk_var.key)
        self.assertEqual(var.value, sdk_var.doubleValue)
        self.assertEqual(var.defaultValue, 0)
        self.assertFalse(var.isDefaulted)

    def test_create_variable_json(self):
        sdk_var = pb2.SDKVariable_PB(
            _id="test id",
            key="test key",
            stringValue='{"strProp": "test value"}',
            type=pb2.VariableType_PB.JSON,
        )

        var = utils.create_variable(sdk_var, {})
        self.assertIsNotNone(var)
        self.assertEqual(var.type, TypeEnum.JSON)
        self.assertIsNone(var._id)
        self.assertEqual(var.key, sdk_var.key)
        self.assertDictEqual(var.value, {"strProp": "test value"})
        self.assertDictEqual(var.defaultValue, {})
        self.assertFalse(var.isDefaulted)

    def test_create_dvcuser_pb_bad_app_build(self):
        user = DevCycleUser(
            user_id="test id",
            appBuild=None,
        )

        result = utils.create_dvcuser_pb(user)
        self.assertIsNotNone(result)
        self.assertEqual(result.user_id, user.user_id)
        self.assertTrue(result.appBuild.isNull)

        user = DevCycleUser(
            user_id="test id",
            appBuild="NotANumberAtAll",
        )

        result = utils.create_dvcuser_pb(user)
        self.assertIsNotNone(result)
        self.assertEqual(result.user_id, user.user_id)
        self.assertTrue(result.appBuild.isNull)

    def test_create_dvcuser_pb(self):
        user = DevCycleUser(
            user_id="test id",
            name="test name",
            email="test email",
            customData={"a": "value1", "b": 0.0, "c": False},
            privateCustomData={"x": "value2", "y": 1234.0, "z": False},
            appBuild="1.17",
            appVersion="1.0.0",
            country="US",
            language=None,
            deviceModel="iPhone X",
        )

        result = utils.create_dvcuser_pb(user)
        self.assertIsNotNone(result)
        self.assertEqual(result.user_id, user.user_id)
        self.assertEqual(result.name.value, user.name)
        self.assertEqual(result.email.value, user.email)
        self.assertTrue(result.language.isNull)
        self.assertEqual(result.appBuild.value, 1.17)

        self.assertEqual(result.customData.value["a"].type, pb2.CustomDataType.Str)
        self.assertEqual(result.customData.value["a"].stringValue, "value1")

        self.assertEqual(
            result.privateCustomData.value["x"].type, pb2.CustomDataType.Str
        )
        self.assertEqual(result.privateCustomData.value["x"].stringValue, "value2")
