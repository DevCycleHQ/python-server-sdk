import logging

import unittest

from devcycle_python_sdk.managers.config_manager import EnvironmentConfigManager

logger = logging.getLogger(__name__)


class EnvironmentConfigManagerTest(unittest.TestCase):
    def test_init(self):
        config_manager = EnvironmentConfigManager(None, None, None)
        self.assertIsNotNone(config_manager)


if __name__ == '__main__':
    unittest.main()
