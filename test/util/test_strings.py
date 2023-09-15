import logging

import unittest

from devcycle_python_sdk.util.strings import slash_join

logger = logging.getLogger(__name__)


class StringsUtilTest(unittest.TestCase):
    def test_slash_join_no_args(self):
        result = slash_join()
        self.assertEqual(result, "")

    def test_slash_join_url_no_slashes(self):
        result = slash_join("http://example.com", "hello", "world")
        self.assertEqual(result, "http://example.com/hello/world")

    def test_slash_join_url_components_with_slashes(self):
        result = slash_join("http://example.com", "/hello", "world/")
        self.assertEqual(result, "http://example.com/hello/world")

    def test_slash_join_url_components_with_numbers(self):
        result = slash_join("http://example.com", "v1", "variable", 1234)
        self.assertEqual(result, "http://example.com/v1/variable/1234")
