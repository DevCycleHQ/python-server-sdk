import logging

import unittest

from devcycle_python_sdk.api.local_bucketing import LocalBucketing

logger = logging.getLogger(__name__)


class LocalBucketingTest(unittest.TestCase):
    def test_init(self):
        local_bucketing = LocalBucketing()
        self.assertIsNotNone(local_bucketing)

    def test_write_read_bytes(self):
        # Test that we can safely pass ASCII strings to the WASM module and read them back
        lb = LocalBucketing()
        test_bytes = "test_bytes".encode("utf-8")
        arg_pointer = lb._new_assembly_script_string(test_bytes)

        echo_func = lb._get_export("echoString")

        result_pointer = echo_func(lb.wasm_store, arg_pointer)

        result_bytes = lb._read_assembly_script_string(result_pointer)
        self.assertEqual(result_bytes, test_bytes)

    def test_write_read_bytes_array(self):
        # Test that we can safely pass byte arrays to the WASM module and read them back
        lb = LocalBucketing()
        test_bytes = "test_bytes".encode("utf-8")
        arg_pointer = lb._new_assembly_script_byte_array(test_bytes)

        echo_func = lb._get_export("echoUint8Array")

        result_pointer = echo_func(lb.wasm_store, arg_pointer)

        result_bytes = lb._read_assembly_script_byte_array(result_pointer)
        self.assertEqual(result_bytes, test_bytes)


if __name__ == "__main__":
    unittest.main()
