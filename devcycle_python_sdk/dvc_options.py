class DVCOptions:
    def __init__(self, enableEdgeDB=False, eventsAPIURI=None, configCDNURI=None, bucketingAPIURI=None):
        self.enableEdgeDB = enableEdgeDB
        self.eventsAPIURI = eventsAPIURI
        self.configCDNURI = configCDNURI
        self.bucketingAPIURI = bucketingAPIURI


class DVCCloudOptions:
    def __init__(self,
                 enable_edge_db: bool = False,
                 events_api_uri: str = "https://events.devcycle.com/",
                 config_cdn_uri: str = "https://config-cdn.devcycle.com/",
                 bucketing_api_uri: str = "https://bucketing-api.devcycle.com/",
                 request_timeout: int = 10000):
        self.enable_edge_db = enable_edge_db
        self.events_API_URI = events_api_uri
        self.config_CDN_URI = config_cdn_uri
        self.bucketing_API_URI = bucketing_api_uri
        self.request_timeout = request_timeout
