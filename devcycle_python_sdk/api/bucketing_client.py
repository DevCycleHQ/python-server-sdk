from os.path import join
from typing import Dict

import requests

from devcycle_python_sdk.dvc_options import DVCCloudOptions
from devcycle_python_sdk.models import Variable, UserData, Feature


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

    def variable(self, key: str, user_data: UserData) -> Variable:
        res = self.session.post(self._url("variables", key), json=user_data.to_json())
        res.raise_for_status()
        data: dict = res.json()

        return Variable(
            id=data.get("_id"),
            key=data.get("key"),
            type=data.get("type"),
            value=data.get("value"),
        )

    def variables(self) -> Dict[str, Variable]:
        raise NotImplementedError

    def features(self) -> Dict[str, Feature]:
        raise NotImplementedError

    def track(self, key: str) -> str:
        raise NotImplementedError
