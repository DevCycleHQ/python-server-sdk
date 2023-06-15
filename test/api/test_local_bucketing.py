import logging

import unittest

from devcycle_python_sdk.api.local_bucketing import LocalBucketing

logger = logging.getLogger(__name__)


class LocalBucketingTest(unittest.TestCase):
    def test_init(self):
        local_bucketing = LocalBucketing()
        self.assertIsNotNone(local_bucketing)


if __name__ == '__main__':
    unittest.main()
