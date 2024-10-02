import ld_eventsource
import ld_eventsource.actions
import ld_eventsource.config

from threading import Thread

class SSEManager:
    def __init__(self, url, handlestate: callable(ld_eventsource.actions.Start),
                 handleerror: callable(ld_eventsource.actions.Fault),
                 handlemessage: callable(ld_eventsource.actions.Event)):
        self.url = url
        self.client: ld_eventsource.SSEClient = ld_eventsource.SSEClient(
            connect=ld_eventsource.config.ConnectStrategy.http(url),
            error_strategy=ld_eventsource.config.ErrorStrategy.always_continue(),

        )
        self.handlestate = handlestate
        self.handleerror = handleerror
        self.handlemessage = handlemessage

        read_thread = Thread(target=self.read_events, args=(handlestate, handleerror, handlemessage))
        read_thread.start()

    def read_events(self,
                    handlestate: callable(ld_eventsource.actions.Start),
                    handleerror: callable(ld_eventsource.actions.Fault),
                    handlemessage: callable(ld_eventsource.actions.Event)):
        self.client.start()
        for event in self.client.all:
            if isinstance(event, ld_eventsource.actions.Start):
                handlestate(event)
            elif isinstance(event, ld_eventsource.actions.Fault):
                handleerror(event)
            elif isinstance(event, ld_eventsource.actions.Event):
                handlemessage(event)
            else:
                print(event)
