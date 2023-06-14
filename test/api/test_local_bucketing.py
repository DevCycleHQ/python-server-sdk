import logging

import unittest

from devcycle_python_sdk.api.local_bucketing import LocalBucketing

logger = logging.getLogger(__name__)


class LocalBucketingTest(unittest.TestCase):
    def test_init(self):
        config_manager = LocalBucketing()


if __name__ == '__main__':
    unittest.main()
