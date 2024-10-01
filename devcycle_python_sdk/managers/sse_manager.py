import requests
import sseclient


class SSEManager:
    def __init__(self, url):
        self.url = url
        self.stream = requests.get(self.url, stream=True)
        self.client: sseclient.SSEClient = sseclient.SSEClient(self.stream)

    def open_stream(self, url):
        self.url = url
        self.stream = requests.get(self.url, stream=True)
        return self.stream

    def open_stream_with_sseclient(self):
        self.client = sseclient.SSEClient(self.stream, char_enc='utf-8')
        return self.client

    def read_events(self, handlestate: callable(sseclient.Event), handleerror: callable(sseclient.Event),
                    handlemessage: callable(sseclient.Event)):
        for event in self.client.events():
            if event.event == 'state':
                handlestate(event)
            elif event.event == 'error':
                handleerror(event)
            elif event.event == 'message':
                handlemessage(event)
            else:
                print(event)