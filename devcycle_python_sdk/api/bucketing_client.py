from os.path import join
from typing import Dict, List

import requests

from devcycle_python_sdk.dvc_options import DVCCloudOptions
from devcycle_python_sdk.models import Variable, UserData, Feature, Event


class BucketingAPIClient:
    def __init__(self, sdk_key: str, options: DVCCloudOptions):
        self.sdk_key = sdk_key
        self.options = options
        self.session = requests.Session()
        self.session.headers = {
            "Authorization": sdk_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.session.max_redirects = 0

    def _url(self, *path_args: str) -> str:
        return join(self.options.bucketing_API_URI, "v1", *path_args)

    def variable(self, key: str, user: UserData) -> Variable:
        res = self.session.post(self._url("variables", key), json=user.to_json())
        res.raise_for_status()
        data: dict = res.json()

        return Variable(
            _id=str(data.get("_id")),
            key=str(data.get("key")),
            type=str(data.get("type")),
            value=data.get("value"),
        )

    def variables(self, user: UserData) -> Dict[str, Variable]:
        res = self.session.post(self._url("variables"), json=user.to_json())
        res.raise_for_status()
        data: dict = res.json()

        result: Dict[str, Variable] = {}
        for key, value in data.items():
            result[key] = Variable(
                _id=str(data.get("_id")),
                key=str(data.get("key")),
                type=str(data.get("type")),
                value=data.get("value"),
            )

        return result

    def features(self, user: UserData) -> Dict[str, Feature]:
        res = self.session.post(self._url("features"), json=user.to_json())
        res.raise_for_status()
        data: dict = res.json()

        result: Dict[str, Feature] = {}
        for key, value in data.items():
            result[key] = Feature(
                _id=value.get("_id"),
                key=value.get("key"),
                type=value.get("type"),
                _variation=value.get("_variation"),
                variationKey=value.get("variationKey"),
                variationName=value.get("variationName"),
                evalReason=value.get("evalReason"),
            )

        return result

    def track(self, user: UserData, events: List[Event]) -> str:
        res = self.session.post(
            self._url("track"),
            json={
                "user": user.to_json(),
                "events": [event.to_json() for event in events],
            },
        )
        res.raise_for_status()
        message = res.json().get("message", "")
        return message
