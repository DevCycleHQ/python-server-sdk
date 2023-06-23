import json
import logging
import unittest

from devcycle_python_sdk.api.local_bucketing import LocalBucketing, WASMAbortError
from devcycle_python_sdk.models.platform_data import default_platform_data
from devcycle_python_sdk.models.user import User
from devcycle_python_sdk.models.variable import TypeEnum
from test.fixture.data import small_config, large_config, special_character_config

logger = logging.getLogger(__name__)


class LocalBucketingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.test_sdk_key = "dvc_server_testkey"
        self.local_bucketing = LocalBucketing(self.test_sdk_key)

    def test_init(self):
        local_bucketing = LocalBucketing(self.test_sdk_key)
        self.assertIsNotNone(local_bucketing)

    def test_write_read_string(self) -> None:
        # Test that we can safely pass ASCII strings to the WASM module and read them back
        test_string = "test_bytes"
        arg_pointer = self.local_bucketing._new_assembly_script_string(test_string)

        echo_func = self.local_bucketing._get_export("echoString")

        result_pointer = echo_func(self.local_bucketing.wasm_store, arg_pointer)

        result_bytes = self.local_bucketing._read_assembly_script_string(result_pointer)
        self.assertEqual(result_bytes, test_string)

    def test_write_read_bytes_array(self) -> None:
        # Test that we can safely pass byte arrays to the WASM module and read them back
        test_bytes = "test_bytes".encode("utf-8")
        arg_pointer = self.local_bucketing._new_assembly_script_byte_array(test_bytes)

        echo_func = self.local_bucketing._get_export("echoUint8Array")

        result_pointer = echo_func(self.local_bucketing.wasm_store, arg_pointer)

        result_bytes = self.local_bucketing._read_assembly_script_byte_array(
            result_pointer
        )
        self.assertEqual(result_bytes, test_bytes)

    def test_abort(self) -> None:
        abort_func = self.local_bucketing._get_export("triggerAbort")

        with self.assertRaises(WASMAbortError) as context:
            abort_func(self.local_bucketing.wasm_store)

        self.assertRegex(
            context.exception.args[0],
            r"Abort in '[^']+':[0-9]+:[0-9]+ -- 'Manual abort triggered'",
        )

    def test_store_config(self) -> None:
        # should store each config with any errors
        self.local_bucketing.store_config(small_config())
        self.local_bucketing.store_config(large_config())
        self.local_bucketing.store_config(special_character_config())

    def test_set_platform_data(self):
        # should set the data without any errors
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)

    def test_set_client_custom_data(self):
        # should set the data without any errors
        client_custom_data = {
            "strProp": "strVal",
            "intProp": 1,
            "floatProp": 1.1,
            "boolProp": True,
            "nullProp": None,
        }
        data_str = json.dumps(client_custom_data)
        self.local_bucketing.set_client_custom_data(data_str)

    def test_get_variable_for_user_protobuf(self):
        self.local_bucketing.store_config(small_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)
        self.local_bucketing.init_event_queue("{}")
        user = User(user_id="test_user_id")
        result = self.local_bucketing.get_variable_for_user_protobuf(user=user,
                                                                     key="string-var",
                                                                     default_value="default value")
        self.assertIsNotNone(result)
        self.assertEqual(result.key, "string-var")
        self.assertEqual(result.type, TypeEnum.STRING)
        self.assertEqual(result.value, "variationOn")
        self.assertFalse(result.isDefaulted)

    def test_get_variable_for_user_protobuf_special_characters(self):
        self.local_bucketing.store_config(special_character_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)
        self.local_bucketing.init_event_queue("{}")
        user = User(user_id="test_user_id")
        result = self.local_bucketing.get_variable_for_user_protobuf(user=user,
                                                                     key="string-var",
                                                                     default_value="default value")
        self.assertIsNotNone(result)
        self.assertEqual(result.key, "string-var")
        self.assertEqual(result.type, TypeEnum.STRING)
        self.assertEqual(result.value, "öé 🐍 ¥ variationOn")
        self.assertFalse(result.isDefaulted)

    def test_get_variable_for_user_protobuf_type_mismatch(self):
        self.local_bucketing.store_config(small_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)
        self.local_bucketing.init_event_queue("{}")
        user = User(user_id="test_user_id")

        # type mismatch is handled inside the WASM and will return
        # no data if the type is not correct
        result = self.local_bucketing.get_variable_for_user_protobuf(user=user,
                                                                     key="string-var",
                                                                     default_value=9999)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
