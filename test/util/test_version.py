import logging

import unittest

from devcycle_python_sdk.util.version import sdk_version

logger = logging.getLogger(__name__)


class VersionTest(unittest.TestCase):
    def test_sdk_version(self):
        version = sdk_version()
        self.assertRegexpMatches(version, r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
