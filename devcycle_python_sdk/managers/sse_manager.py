import threading

import ld_eventsource
import ld_eventsource.actions
import logging
import ld_eventsource.config
from typing import Callable

logger = logging.getLogger(__name__)


class SSEManager:
    def __init__(
        self,
        handle_state: Callable[[ld_eventsource.actions.Start], None],
        handle_error: Callable[[ld_eventsource.actions.Fault], None],
        handle_message: Callable[[ld_eventsource.actions.Event], None],
    ):
        self.client: ld_eventsource.SSEClient = None
        self.url = ""
        self.handle_state = handle_state
        self.handle_error = handle_error
        self.handle_message = handle_message

        self.read_thread = threading.Thread(
            target=self.read_events,
            args=(self.handle_state, self.handle_error, self.handle_message),
        )

    def read_events(
        self,
        handle_state: Callable[[ld_eventsource.actions.Start], None],
        handle_error: Callable[[ld_eventsource.actions.Fault], None],
        handle_message: Callable[[ld_eventsource.actions.Event], None],
    ):
        self.client.start()
        try:
            for event in self.client.all:
                if isinstance(event, ld_eventsource.actions.Start):
                    handle_state(event)
                elif isinstance(event, ld_eventsource.actions.Fault):
                    handle_error(event)
                elif isinstance(event, ld_eventsource.actions.Event):
                    handle_message(event)
        except Exception as e:
            logger.debug(f"DevCycle: failed to read SSE message: {e}")

    def update(self, config: dict):
        if self.use_new_config(config["sse"]):
            self.url = config["sse"]["hostname"] + config["sse"]["path"]
            if self.client is not None:
                self.client.close()
            if self.read_thread.is_alive():
                self.read_thread.join()
            self.client = ld_eventsource.SSEClient(
                connect=ld_eventsource.config.ConnectStrategy.http(self.url),
                error_strategy=ld_eventsource.config.ErrorStrategy.CONTINUE,
            )
            self.read_thread = threading.Thread(
                target=self.read_events,
                args=(self.handle_state, self.handle_error, self.handle_message),
            )
            self.read_thread.start()

    def use_new_config(self, config: dict) -> bool:
        new_url = config["hostname"] + config["path"]
        if self.url == "" or self.url is None and new_url != "":
            return True
        return self.url != new_url
