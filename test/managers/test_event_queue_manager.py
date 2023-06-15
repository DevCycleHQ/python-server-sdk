import logging

import unittest

from devcycle_python_sdk.managers.event_queue_manager import EventQueueManager

logger = logging.getLogger(__name__)


class EventQueueManagerTest(unittest.TestCase):
    def test_init(self):
        eq_manager = EventQueueManager(None, None, None)
        self.assertIsNotNone(eq_manager)


if __name__ == '__main__':
    unittest.main()
