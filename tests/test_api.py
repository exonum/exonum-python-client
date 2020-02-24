# pylint: disable=missing-docstring, protected-access
# type: ignore

import unittest
from unittest.mock import patch, Mock
import random

random.seed(0)

from exonum_client.api import Api, PublicApi, PrivateApi, ServiceApi
from .testing_utils import *


class TestApi(unittest.TestCase):
    def setUp(self):
        self.api = Api(EXONUM_IP, EXONUM_PUBLIC_PORT, EXONUM_PROTO)

    @patch("exonum_client.api.Api.get", new=mock_requests_get)
    def test_get(self):
        url = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PRIVATE_PORT)
        url += SYSTEM_ENDPOINT_POSTFIX.format("stats")
        resp = self.api.get(url)
        self.assertEqual(resp.status_code, 200)

    @patch("exonum_client.api.Api.post", new=mock_requests_post)
    def test_post(self):
        url = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PRIVATE_PORT)
        url += SYSTEM_ENDPOINT_POSTFIX.format("shutdown")
        resp = self.api.post(url)
        self.assertEqual(resp.status_code, 200)


class TestPublicApi(unittest.TestCase):
    def setUp(self):
        self.public_api = PublicApi(EXONUM_IP, EXONUM_PUBLIC_PORT, EXONUM_PROTO)

    @patch("exonum_client.api.PublicApi.post", new=mock_requests_post)
    def test_send_transaction(self):
        resp = self.public_api.send_transaction(Mock())
        self.assertEqual(resp.status_code, 200)

    @patch("exonum_client.api.PublicApi.get", new=mock_requests_get)
    def test_get_block(self):
        height = random.randrange(0, 20)
        resp = self.public_api.get_block(height)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["height"], height)

        height = random.randrange(-10, 0)
        resp = self.public_api.get_block(height)
        self.assertEqual(resp.status_code, 400)

        height = "not an integer"
        resp = self.public_api.get_block(height)
        self.assertEqual(resp.status_code, 400)

    @patch("exonum_client.api.PublicApi.get", new=mock_requests_get)
    def test_get_blocks(self):
        count = random.randrange(0, 10)
        resp = self.public_api.get_blocks(count)
        self.assertEqual(resp.status_code, 200)

        count = random.randrange(-10, 0)
        resp = self.public_api.get_blocks(count)
        self.assertEqual(resp.status_code, 400)

        count = "not an integer"
        resp = self.public_api.get_blocks(count)
        self.assertEqual(resp.status_code, 400)

        count = random.randrange(0, 20)
        latest = random.randrange(0, 100)
        earliest = latest + 10
        resp = self.public_api.get_blocks(count, latest=latest, earliest=earliest)
        self.assertEqual(resp.status_code, 200)

    @patch("exonum_client.api.PublicApi.get", new=mock_requests_get)
    def test_get_tx_info(self):
        tx_hash = "-" * 64
        resp = self.public_api.get_tx_info(tx_hash)
        self.assertEqual(resp.status_code, 400)

        tx_hash = random_alphanumeric_string()
        resp = self.public_api.get_tx_info(tx_hash)
        self.assertEqual(resp.status_code, 200)


class TestPrivateApi(unittest.TestCase):
    def setUp(self):
        self.private_api = PrivateApi(EXONUM_IP, EXONUM_PRIVATE_PORT, EXONUM_PROTO)

    @patch("exonum_client.api.PrivateApi.get", new=mock_requests_get)
    def test_get_info(self):
        resp = self.private_api.get_info()
        self.assertEqual(resp.status_code, 200)

    @patch("exonum_client.api.PrivateApi.get", new=mock_requests_get)
    def test_get_stats(self):
        resp = self.private_api.get_stats()
        self.assertEqual(resp.status_code, 200)

    @patch("exonum_client.api.PrivateApi.post", new=mock_requests_post)
    def test_add_peer(self):
        address = "address"
        public_key = "public_key"
        resp = self.private_api.add_peer(address, public_key)
        self.assertEqual(resp.status_code, 200)

    @patch("exonum_client.api.PrivateApi.post", new=mock_requests_post)
    def test_shutdown(self):
        resp = self.private_api.shutdown()
        self.assertEqual(resp.status_code, 200)

    @patch("exonum_client.api.PrivateApi.post", new=mock_requests_post)
    def test_set_consensus_interaction(self):
        enabled = bool(random.randrange(0, 2))
        resp = self.private_api.set_consensus_interaction(enabled)
        self.assertEqual(resp.status_code, 200)


class TestServiceApi(unittest.TestCase):
    def setUp(self):
        self.public_api = ServiceApi("service", EXONUM_IP, EXONUM_PUBLIC_PORT, EXONUM_PROTO)
        self.private_api = ServiceApi("service", EXONUM_IP, EXONUM_PRIVATE_PORT, EXONUM_PROTO)

    def test_service_endpoint(self):
        exonum_public_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PUBLIC_PORT)
        exonum_private_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PRIVATE_PORT)

        service = "service"
        endpoint = "endpoint"

        # Test a public endpoint generation:
        got_endpoint = self.public_api.service_endpoint(endpoint)

        expected_public_endpoint = exonum_public_base + SERVICE_ENDPOINT_POSTFIX.format(service, endpoint)

        self.assertEqual(got_endpoint, expected_public_endpoint)

        # Test a private endpoint generation:
        got_endpoint = self.private_api.service_endpoint(endpoint)

        expected_private_endpoint = exonum_private_base + SERVICE_ENDPOINT_POSTFIX.format(service, endpoint)

        self.assertEqual(got_endpoint, expected_private_endpoint)
