import logging

import unittest

from devcycle_python_sdk.util.version import sdk_version

logger = logging.getLogger(__name__)


class VersionTest(unittest.TestCase):
    def test_sdk_version(self):
        expected_version = "2.0.1"
        version = sdk_version()
        self.assertEqual(version, expected_version)


if __name__ == '__main__':
    unittest.main()
