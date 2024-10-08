import threading

import ld_eventsource
import ld_eventsource.actions
import ld_eventsource.config
from typing import Callable


class SSEManager:
    def __init__(
        self,
        handlestate: Callable[[ld_eventsource.actions.Start], None],
        handleerror: Callable[[ld_eventsource.actions.Fault], None],
        handlemessage: Callable[[ld_eventsource.actions.Event], None],
    ):
        self.client: ld_eventsource.SSEClient = None
        self.url = ""
        self.handlestate = handlestate
        self.handleerror = handleerror
        self.handlemessage = handlemessage

        self.read_thread = threading.Thread(
            target=self.read_events,
            args=(self.handlestate, self.handleerror, self.handlemessage),
        )

    def read_events(
        self,
        handlestate: Callable[[ld_eventsource.actions.Start], None],
        handleerror: Callable[[ld_eventsource.actions.Fault], None],
        handlemessage: Callable[[ld_eventsource.actions.Event], None],
    ):
        self.client.start()
        for event in self.client.all:
            if isinstance(event, ld_eventsource.actions.Start):
                handlestate(event)
            elif isinstance(event, ld_eventsource.actions.Fault):
                handleerror(event)
            elif isinstance(event, ld_eventsource.actions.Event):
                handlemessage(event)

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
                args=(self.handlestate, self.handleerror, self.handlemessage),
            )
            self.read_thread.start()

    def use_new_config(self, config: dict) -> bool:
        new_url = config["hostname"] + config["path"]
        if self.url == "" or self.url is None and new_url != "":
            return True
        return self.url != new_url
