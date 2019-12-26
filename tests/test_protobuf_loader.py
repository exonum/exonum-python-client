import unittest
from unittest.mock import patch
import sys
import os


from exonum_client.module_manager import ModuleManager
from exonum_client.protobuf_loader import ProtobufLoader
from exonum_client.client import ExonumClient
from .testing_utils import *


class TestProtobufLoader(unittest.TestCase):
    def setUp(self):
        self.client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )

    def test_protobuf_loader_creates_temp_folder(self):
        # Test that the proto directory is created and added to sys.path:
        proto_dir = None

        with self.client.protobuf_loader() as loader:
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

        loader = self.client.protobuf_loader()
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

        with self.client.protobuf_loader() as loader_1:
            with self.client.protobuf_loader() as loader_2:
                self.assertEqual(loader_1, loader_2)

    def test_protobuf_loader_created_twice_different_client(self):
        # Test that if we try to create more than one ProtobufLoader entity
        # with different clients, an exception is raised:

        client_2 = ExonumClient(
            hostname="127.0.0.2", public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )

        with self.client.protobuf_loader() as _loader:
            with self.assertRaises(ValueError):
                client_2.protobuf_loader()

    @patch("exonum_client.api.ProtobufApi.get", new=mock_requests_get)
    def test_main_sources_download(self):
        with self.client.protobuf_loader() as loader:
            loader.load_main_proto_files()

            _runtime_mod = ModuleManager.import_main_module("runtime")

    @patch("exonum_client.api.ProtobufApi.get", new=mock_requests_get)
    def test_service_sources_download(self):
        with self.client.protobuf_loader() as loader:
            loader.load_main_proto_files()
            loader.load_service_proto_files(0, "exonum-supervisor", "0.11.0")

            _service_module = ModuleManager.import_service_module("exonum-supervisor", "0.11.0", "service")
