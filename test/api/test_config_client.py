import logging
import unittest
import uuid
from os.path import join
from http import HTTPStatus

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
from test.fixture.data import small_config_json

logger = logging.getLogger(__name__)


class ConfigAPIClientTest(unittest.TestCase):
    def setUp(self) -> None:
        self.sdk_key = "dvc_server_" + str(uuid.uuid4())
        self.config_url = (
            join(
                "https://config-cdn.devcycle.com/",
                "config",
                "v1",
                "server",
                self.sdk_key,
            )
            + ".json"
        )

        options = DevCycleLocalOptions(config_retry_delay_ms=0)
        self.test_client = ConfigAPIClient(self.sdk_key, options)
        self.test_etag = str(uuid.uuid4())
        self.test_config_json: dict = small_config_json()

    @responses.activate
    def test_get_config(self):
        new_etag = str(uuid.uuid4())
        responses.add(
            responses.GET,
            self.config_url,
            headers={"ETag": new_etag},
            json=self.test_config_json,
        )
        result, etag = self.test_client.get_config(config_etag=self.test_etag)
        self.assertDictEqual(result, self.test_config_json)
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
        result, etag = self.test_client.get_config(config_etag=self.test_etag)

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
            headers={"ETag": self.test_etag},
            json=self.test_config_json,
        )
        result, etag = self.test_client.get_config(config_etag=self.test_etag)
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

        new_config, new_etag = self.test_client.get_config(config_etag=self.test_etag)
        self.assertIsNone(new_config)
        self.assertEqual(new_etag, self.test_etag)
