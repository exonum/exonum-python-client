from typing import List
import unittest
from unittest.mock import patch
import sys
import os

from exonum_client.client import ExonumClient
from exonum_client.module_manager import ModuleManager
from exonum_client.protobuf_loader import ProtobufLoader, ProtobufProviderInterface, ProtoFile

from .module_user import ModuleUserTestCase

EXONUM_PROTO = "http"
EXONUM_IP = "127.0.0.1"
EXONUM_PUBLIC_PORT = "8080"
EXONUM_PRIVATE_PORT = "8081"
EXONUM_URL_BASE = "{}://{}:{}/"

SYSTEM_ENDPOINT_POSTFIX = "api/system/v1/{}"
SERVICE_ENDPOINT_POSTFIX = "api/services/{}/{}"


def ok_response():
    from requests.models import Response

    response = Response()
    response.code = "OK"
    response.status_code = 200

    return response


def mock_requests_get(url, params=None):
    exonum_public_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PUBLIC_PORT)

    healthcheck_endpoint = exonum_public_base + SYSTEM_ENDPOINT_POSTFIX.format("healthcheck")
    stats_endpoint = exonum_public_base + SYSTEM_ENDPOINT_POSTFIX.format("stats")
    user_agent_endpoint = exonum_public_base + SYSTEM_ENDPOINT_POSTFIX.format("user_agent")

    responses = {
        # System endpoints:
        (healthcheck_endpoint, "None"): ok_response(),
        (stats_endpoint, "None"): ok_response(),
        (user_agent_endpoint, "None"): ok_response(),
    }

    return responses[(url, str(params))]


class MockProtobufProvider(ProtobufProviderInterface):
    def get_main_proto_sources(self) -> List[ProtoFile]:
        base_path = "tests/proto_dir/proto/main"

        return self._get(base_path)

    def get_proto_sources_for_artifact(self, _id: int, _name: str) -> List[ProtoFile]:
        base_path = "tests/proto_dir/proto/exonum_cryptocurrency_advanced_0_11_0"

        return self._get(base_path)

    @staticmethod
    def _get(base_path: str) -> List[ProtoFile]:
        results = []

        for file_name in os.listdir(base_path):
            file_path = os.path.join(base_path, file_name)
            with open(file_path, "r") as source_file:
                file_content = source_file.read()

            results.append(ProtoFile(name=file_name, content=file_content))

        return results


class TestProtobufLoader(ModuleUserTestCase):
    def test_protobuf_loader_creates_temp_folder(self):
        # Test that the proto directory is created and added to sys.path:
        proto_dir = None

        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )
        client.set_protobuf_provider(MockProtobufProvider())

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
        exonum_client.set_protobuf_provider(MockProtobufProvider())
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
        client.set_protobuf_provider(MockProtobufProvider())

        with client.protobuf_loader() as loader_1:
            with client.protobuf_loader() as loader_2:
                self.assertEqual(loader_1, loader_2)

    def test_protobuf_loader_created_twice_different_client(self):
        # Test that if we try to create more than one ProtobufLoader entity
        # with different clients, an exception is raised:

        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )
        client.set_protobuf_provider(MockProtobufProvider())

        client_2 = ExonumClient(
            hostname="127.0.0.2", public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )
        client_2.set_protobuf_provider(MockProtobufProvider())

        with client.protobuf_loader() as _loader:
            with self.assertRaises(ValueError):
                client_2.protobuf_loader()

    def test_main_sources_download(self):
        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )
        client.set_protobuf_provider(MockProtobufProvider())
        with client.protobuf_loader() as loader:
            loader.load_main_proto_files()

            _helpers_mod = ModuleManager.import_main_module("helpers")

    def test_service_sources_download(self):
        client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )
        client.set_protobuf_provider(MockProtobufProvider())
        with client.protobuf_loader() as loader:
            loader.load_main_proto_files()
            loader.load_service_proto_files(0, "cryptocurrency-advanced")

            _service_module = ModuleManager.import_service_module("cryptocurrency-advanced", "service")


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
