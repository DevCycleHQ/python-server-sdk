import logging
import uuid
import unittest
from unittest.mock import MagicMock

from devcycle_python_sdk import DevCycleLocalOptions

logger = logging.getLogger(__name__)


class EventQueueManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sdk_key = "dvc_server_" + str(uuid.uuid4())
        self.test_local_bucketing = MagicMock()
        self.test_options = DevCycleLocalOptions(disable_automatic_event_logging=False, disable_custom_event_logging=False)

    def tearDown(self) -> None:
        pass


if __name__ == "__main__":
    unittest.main()
