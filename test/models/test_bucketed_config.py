import json
import logging
import unittest

from devcycle_python_sdk.models.bucketed_config import BucketedConfig
from test.fixture.data import bucketed_config, bucketed_config_minimal

logger = logging.getLogger(__name__)


class BucketedConfigTest(unittest.TestCase):
    def test_bucketed_config_all_fields(self) -> None:
        bucketed_config_parsed = json.loads(bucketed_config())
        result = BucketedConfig.from_json(bucketed_config_parsed)

        # Fields are already checked in the local bucketing tests, no need to repeat here
        self.assertIsNotNone(result)

    def test_bucketed_config_minimal(self) -> None:
        bucketed_config_parsed = json.loads(bucketed_config_minimal())
        result = BucketedConfig.from_json(bucketed_config_parsed)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
