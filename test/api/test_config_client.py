import logging
import unittest
import uuid
from http import HTTPStatus
from datetime import datetime
from email.utils import formatdate
from time import mktime

import requests
import responses
from responses.registries import OrderedRegistry

from devcycle_python_sdk.api.config_client import ConfigAPIClient
from devcycle_python_sdk.options import DevCycleLocalOptions
from devcycle_python_sdk.exceptions import (
    APIClientError,
    APIClientUnauthorizedError,
    NotFoundError,
)
from devcycle_python_sdk.util.strings import slash_join
from test.fixture.data import small_config_json

logger = logging.getLogger(__name__)


class ConfigAPIClientTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sdk_key = "dvc_server_" + str(uuid.uuid4())
        self.config_url = (
            slash_join(
                "https://config-cdn.devcycle.com/",
                "config",
                "v2",
                "server",
                self.sdk_key,
            )
            + ".json"
        )

        options = DevCycleLocalOptions(config_retry_delay_ms=0)
        self.test_client = ConfigAPIClient(self.sdk_key, options)
        now = datetime.now()
        stamp = mktime(now.timetuple())
        self.test_lastmodified = formatdate(timeval=stamp, localtime=False, usegmt=True)
        self.test_etag = str(uuid.uuid4())
        self.test_config_json: dict = small_config_json()

    def test_url(self):
        self.assertEqual(self.test_client.config_file_url, self.config_url)

    @responses.activate
    def test_get_config(self):
        new_etag = str(uuid.uuid4())
        now = datetime.now()
        stamp = mktime(now.timetuple())
        new_lastmodified = formatdate(timeval=stamp, localtime=False, usegmt=True)
        responses.add(
            responses.GET,
            self.config_url,
            headers={"ETag": new_etag, "Last-Modified": new_lastmodified},
            json=self.test_config_json,
        )
        result, etag, lastmodified = self.test_client.get_config(
            config_etag=self.test_etag, last_modified=self.test_lastmodified
        )
        self.assertDictEqual(result, self.test_config_json)
        self.assertEqual(lastmodified, new_lastmodified)
        self.assertEqual(etag, new_etag)

    @responses.activate(registry=OrderedRegistry)
    def test_get_config_retries(self):
        responses.add(
            responses.GET,
            self.config_url,
            status=500,
        )
        responses.add(
            responses.GET,
            self.config_url,
            headers={"ETag": self.test_etag},
            json=self.test_config_json,
        )
        result, etag, lastmodified = self.test_client.get_config(
            config_etag=self.test_etag
        )

        self.assertDictEqual(result, self.test_config_json)
        self.assertEqual(etag, self.test_etag)

    @responses.activate(registry=OrderedRegistry)
    def test_get_config_retries_network_error(self):
        responses.add(
            responses.GET,
            self.config_url,
            body=requests.exceptions.ConnectionError("Network Error"),
        )
        responses.add(
            responses.GET,
            self.config_url,
            headers={"ETag": self.test_etag, "Last-Modified": self.test_lastmodified},
            json=self.test_config_json,
        )
        result, etag, last_modified = self.test_client.get_config(
            config_etag=self.test_etag
        )
        self.assertDictEqual(result, self.test_config_json)
        self.assertEqual(etag, self.test_etag)

    @responses.activate(registry=OrderedRegistry)
    def test_get_config_retries_exceeded(self):
        for i in range(2):
            responses.add(
                responses.GET,
                self.config_url,
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        with self.assertRaises(APIClientError):
            self.test_client.get_config(config_etag=self.test_etag)

    @responses.activate
    def test_get_config_not_found(self):
        for i in range(2):
            responses.add(
                responses.GET,
                self.config_url,
                status=HTTPStatus.NOT_FOUND,
            )
        with self.assertRaises(NotFoundError):
            self.test_client.get_config(config_etag=self.test_etag)

    @responses.activate
    def test_get_config_unauthorized(self):
        for i in range(2):
            responses.add(
                responses.GET,
                self.config_url,
                status=HTTPStatus.UNAUTHORIZED,
            )
        with self.assertRaises(APIClientUnauthorizedError):
            self.test_client.get_config(config_etag=self.test_etag)

    @responses.activate
    def test_get_config_not_modified(self):
        responses.add(
            responses.GET,
            self.config_url,
            status=HTTPStatus.NOT_MODIFIED,
        )

        new_config, new_etag, last_modified = self.test_client.get_config(
            config_etag=self.test_etag
        )
        self.assertIsNone(new_config)
        self.assertEqual(new_etag, self.test_etag)
