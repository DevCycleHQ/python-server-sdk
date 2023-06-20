import logging

import unittest

from devcycle_python_sdk.api.local_bucketing import LocalBucketing, WASMAbortError

logger = logging.getLogger(__name__)


class LocalBucketingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.local_bucketing = LocalBucketing()

    def test_init(self):
        local_bucketing = LocalBucketing()
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

        self.assertRegexpMatches(
            context.exception.args[0],
            r"Abort in '[^']+':[0-9]+:[0-9]+ -- 'Manual abort triggered'",
        )


if __name__ == "__main__":
    unittest.main()
