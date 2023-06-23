import json
import logging

from devcycle_python_sdk.dvc_options import DevCycleLocalOptions
from devcycle_python_sdk.api.local_bucketing import LocalBucketing

logger = logging.getLogger(__name__)


class EventQueueManager:
    def __init__(
        self,
        sdk_key: str,
        options: DevCycleLocalOptions,
        local_bucketing: LocalBucketing,
    ):
        self.sdk_key = sdk_key
        self.options = options
        self.local_bucketing = local_bucketing

        # TODO setup proper options for the event queue
        event_options: dict = {}
        event_options_json = json.dumps(event_options)
        self.local_bucketing.init_event_queue(event_options_json)

    def close(self):
        # TODO cleanup event queue
        pass
