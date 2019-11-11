# pylint: disable=missing-docstring, protected-access
# type: ignore

import unittest
from unittest.mock import patch
import sys
import os

from exonum_client.client import ExonumClient
from exonum_client.module_manager import ModuleManager
from exonum_client.protobuf_loader import ProtobufLoader

EXONUM_PROTO = "http"
EXONUM_IP = "127.0.0.1"
EXONUM_PUBLIC_PORT = "8080"
EXONUM_PRIVATE_PORT = "8081"
EXONUM_URL_BASE = "{}://{}:{}/"

SYSTEM_ENDPOINT_POSTFIX = "api/system/v1/{}"
SERVICE_ENDPOINT_POSTFIX = "api/services/{}/{}"


def proto_sources_response(service):
    from requests.models import Response

    with open("tests/api_responses/proto_sources_{}.json".format(service)) as file:
        content = file.read()

        response = Response()
        response.code = "OK"
        response.status_code = 200
        response.headers = {"content-type": "application/json; charset=utf8"}
        response._content = bytes(content, "utf-8")

        return response


def ok_response():
    from requests.models import Response

    response = Response()
    response.code = "OK"
    response.status_code = 200

    return response


def mock_requests_get(url, params=None):
    exonum_public_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PUBLIC_PORT)
    _exonum_private_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PRIVATE_PORT)

    proto_sources_endpoint = exonum_public_base + SYSTEM_ENDPOINT_POSTFIX.format("proto-sources")

    healthcheck_endpoint = exonum_public_base + SYSTEM_ENDPOINT_POSTFIX.format("healthcheck")
    stats_endpoint = exonum_public_base + SYSTEM_ENDPOINT_POSTFIX.format("stats")
    user_agent_endpoint = exonum_public_base + SYSTEM_ENDPOINT_POSTFIX.format("user_agent")

    responses = {
        # Proto sources endpoints.
        # Proto sources without params (main sources):
        (proto_sources_endpoint, "None"): proto_sources_response("main"),
        # Proto sources for the supervisor service:
        (proto_sources_endpoint, "{'artifact': '0:exonum-supervisor:0.11.0'}"): proto_sources_response("supervisor"),
        # System endpoints:
        (healthcheck_endpoint, "None"): ok_response(),
        (stats_endpoint, "None"): ok_response(),
        (user_agent_endpoint, "None"): ok_response(),
    }

    return responses[(url, str(params))]


class TestProtobufLoader(unittest.TestCase):
    def test_protobuf_loader_creates_temp_folder(self):
        # Test that the proto directory is created and added to sys.path:
        proto_dir = None

        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )

        with client.protobuf_loader() as loader:
            proto_dir = loader._proto_dir
            self.assertTrue(os.path.isdir(proto_dir))
            self.assertTrue(os.path.exists(proto_dir))
            self.assertTrue(proto_dir in sys.path)

        # Test that everything is cleaned up after use:
        self.assertFalse(os.path.isdir(proto_dir))
        self.assertFalse(os.path.exists(proto_dir))
        self.assertFalse(proto_dir in sys.path)

    def test_protobuf_loader_creates_temp_folder_manual_init(self):
        # Test that the proto directory is created and added to sys.path:

        exonum_client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )
        loader = exonum_client.protobuf_loader()
        loader.initialize()

        proto_dir = loader._proto_dir

        self.assertTrue(os.path.isdir(proto_dir))
        self.assertTrue(os.path.exists(proto_dir))
        self.assertTrue(proto_dir in sys.path)

        loader.deinitialize()

        # Test that everything is cleaned up after use:
        self.assertFalse(os.path.isdir(proto_dir))
        self.assertFalse(os.path.exists(proto_dir))
        self.assertFalse(proto_dir in sys.path)

    def test_protobuf_loader_no_client(self):
        # Test that if we try to create ProtobufLoader without client,
        # an exception is raised:

        with self.assertRaises(ValueError):
            ProtobufLoader()

    def test_protobuf_loader_created_twice(self):
        # Test that if we try to create more than one ProtobufLoader entity,
        # in fact only one entity is created:

        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )

        with client.protobuf_loader() as loader_1:
            with client.protobuf_loader() as loader_2:
                self.assertEqual(loader_1, loader_2)

    def test_protobuf_loader_created_twice_different_client(self):
        # Test that if we try to create more than one ProtobufLoader entity
        # with different clients, an exception is raised:

        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )

        client_2 = ExonumClient(
            hostname="127.0.0.2", public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )

        with client.protobuf_loader() as _loader:
            with self.assertRaises(ValueError):
                client_2.protobuf_loader()

    @patch("exonum_client.client._get", new=mock_requests_get)
    def test_main_sources_download(self):
        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )
        with client.protobuf_loader() as loader:
            loader.load_main_proto_files()

            _runtime_mod = ModuleManager.import_main_module("runtime")

    @patch("exonum_client.client._get", new=mock_requests_get)
    def test_service_sources_download(self):
        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )
        with client.protobuf_loader() as loader:
            loader.load_main_proto_files()
            loader.load_service_proto_files(0, "exonum-supervisor:0.11.0")

            _service_module = ModuleManager.import_service_module("exonum-supervisor:0.11.0", "service")


class TestExonumClient(unittest.TestCase):
    # This test case replaces the get function from the Exonum client with the mock one.
    # Thus testing of HTTP interacting could be done without actual Exonum client:

    @patch("exonum_client.client._get", new=mock_requests_get)
    def test_helthcheck(self):
        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )
        resp = client.health_info()
        self.assertEqual(resp.status_code, 200)

    @patch("exonum_client.client._get", new=mock_requests_get)
    def test_stats(self):
        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )
        resp = client.stats()
        self.assertEqual(resp.status_code, 200)

    @patch("exonum_client.client._get", new=mock_requests_get)
    def test_user_agent(self):
        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )
        resp = client.user_agent()
        self.assertEqual(resp.status_code, 200)

    def test_service_endpoint(self):
        exonum_public_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PUBLIC_PORT)
        exonum_private_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PRIVATE_PORT)

        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )
        service = "service"
        endpoint = "endpoint"

        # Test a public endpoint generation:
        got_endpoint = client.service_endpoint(service, endpoint)

        expected_public_endpoint = exonum_public_base + SERVICE_ENDPOINT_POSTFIX.format(service, endpoint)

        self.assertEqual(got_endpoint, expected_public_endpoint)

        # Test a private endpoint generation:
        got_endpoint = client.service_endpoint(service, endpoint, private=True)

        expected_private_endpoint = exonum_private_base + SERVICE_ENDPOINT_POSTFIX.format(service, endpoint)

        self.assertEqual(got_endpoint, expected_private_endpoint)

    # TODO add more tests;
    # send_transaction
    # send_transactions
    # get_block
    # get_blocks
    # get_tx_info
    # get_service
    # Subscriber tests
