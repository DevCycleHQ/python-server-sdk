import logging

import unittest

from devcycle_python_sdk.models.variable import Variable, TypeEnum
import devcycle_python_sdk.protobuf.helper as helper
import devcycle_python_sdk.protobuf.variableForUserParams_pb2 as pb2

logger = logging.getLogger(__name__)


class VersionTest(unittest.TestCase):
    def test_create_nullable_double(self):
        result = helper.create_nullable_double(None)
        self.assertIsNotNone(result)
        self.assertTrue(result.isNull)

        result = helper.create_nullable_double(99.0)
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull)
        self.assertEqual(result.value, 99.0)

    def test_create_nullable_string(self):
        result = helper.create_nullable_string(None)
        self.assertIsNotNone(result)
        self.assertTrue(result.isNull)

        result = helper.create_nullable_string("")
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull)
        self.assertEqual(result.value, "")

        result = helper.create_nullable_string("test value")
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull)
        self.assertEqual(result.value, "test value")

    def test_create_nullable_custom_data(self):
        result = helper.create_nullable_custom_data(None)
        self.assertIsNotNone(result)
        self.assertTrue(result.isNull)

        result = helper.create_nullable_custom_data(dict())
        self.assertIsNotNone(result)
        self.assertTrue(result.isNull)

        result = helper.create_nullable_custom_data({"strProp": "test value"})
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull)
        self.assertEqual(result.value["strProp"].type, pb2.CustomDataType.Str)
        self.assertEqual(result.value["strProp"].stringValue, "test value")

        result = helper.create_nullable_custom_data({"boolProp": False})
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull)
        self.assertEqual(result.value["boolProp"].type, pb2.CustomDataType.Bool)
        self.assertEqual(result.value["boolProp"].boolValue, False)

        result = helper.create_nullable_custom_data({"numProp": 1234.0})
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

        var = helper.create_variable(sdk_var, "default value")
        self.assertIsNotNone(var)
        self.assertEqual(var.type, TypeEnum.STRING)
        self.assertEqual(var._id, sdk_var._id)
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

        var = helper.create_variable(sdk_var, False)
        self.assertIsNotNone(var)
        self.assertEqual(var.type, TypeEnum.BOOLEAN)
        self.assertEqual(var._id, sdk_var._id)
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

        var = helper.create_variable(sdk_var, 0)
        self.assertIsNotNone(var)
        self.assertEqual(var.type, TypeEnum.NUMBER)
        self.assertEqual(var._id, sdk_var._id)
        self.assertEqual(var.key, sdk_var.key)
        self.assertEqual(var.value, sdk_var.doubleValue)
        self.assertEqual(var.defaultValue, 0)
        self.assertFalse(var.isDefaulted)

    def test_create_variable_json(self):
        sdk_var = pb2.SDKVariable_PB(
            _id="test id",
            key="test key",
            stringValue="{\"strProp\": \"test value\"}",
            type=pb2.VariableType_PB.JSON,
        )

        var = helper.create_variable(sdk_var, {})
        self.assertIsNotNone(var)
        self.assertEqual(var.type, TypeEnum.JSON)
        self.assertEqual(var._id, sdk_var._id)
        self.assertEqual(var.key, sdk_var.key)
        self.assertDictEqual(var.value, {"strProp": "test value"})
        self.assertDictEqual(var.defaultValue, {})
        self.assertFalse(var.isDefaulted)
