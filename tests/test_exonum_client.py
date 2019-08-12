import unittest
from unittest.mock import patch
import sys
import os

from exonum.client import ExonumClient
from exonum.module_manager import ModuleManager

EXONUM_PROTO = 'http'
EXONUM_IP = '127.0.0.1'
EXONUM_PUBLIC_PORT = '8080'
EXONUM_PRIVATE_PORT = '8081'
EXONUM_URL_BASE = '{}://{}:{}/'

SYSTEM_ENDPOINT_POSTFIX = 'api/system/v1/{}'

def proto_sources_response(service):
    from requests.models import Response

    with open('tests/api_responses/proto_sources_{}.json'.format(service)) as file:
        content = file.read()

        response = Response()
        response.code = 'OK'
        response.status_code = 200
        response._content = bytes(content, 'utf-8')

        return response



def mock_requests_get(url, params=None):
    exonum_public_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PUBLIC_PORT)
    exonum_private_base = EXONUM_URL_BASE.format(EXONUM_PROTO, EXONUM_IP, EXONUM_PRIVATE_PORT)

    proto_sources_endpoint = exonum_public_base + SYSTEM_ENDPOINT_POSTFIX.format('proto-sources')


    responses = {
        # Proto sources endpoints

        # Proto sources without params (main sources)
        (proto_sources_endpoint, "None"): proto_sources_response('main'),
        # Proto sources for supervisor service
        (proto_sources_endpoint, "{'artifact': '0:exonum-supervisor:0.11.0'}"): proto_sources_response('supervisor')

    }

    return responses[(url, str(params))]

class TestExonumClient(unittest.TestCase):
    # This test case replaces get function from exonum client with the mock one.
    # Thus testing of HTTP interacting could be done without actual exonum client.

    def setUp(cls):
        # Unload any previously loaded `exonum_main` modules from other tests
        loaded_modules = list(sys.modules.keys())
        for module in loaded_modules:
            if module.startswith('exonum_modules'):
                del sys.modules[module]

    def test_client_creates_temp_folder(self):
        # Test that proto directory is created and added to sys.path

        with ExonumClient(hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT,
                          private_api_port=EXONUM_PRIVATE_PORT) as client:
            self.assertTrue(os.path.isdir(client.proto_dir))
            self.assertTrue(os.path.exists(client.proto_dir))
            self.assertTrue(client.proto_dir in sys.path)

        # Test that everything is cleaned up after use
        self.assertFalse(os.path.isdir(client.proto_dir))
        self.assertFalse(os.path.exists(client.proto_dir))
        self.assertFalse(client.proto_dir in sys.path)

    @patch('exonum.client.get', new=mock_requests_get)
    def test_main_sources_download(self):
        with ExonumClient(hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT,
                          private_api_port=EXONUM_PRIVATE_PORT) as client:
            client.load_main_proto_files()

            runtime_mod = ModuleManager.import_main_module('runtime')

    @patch('exonum.client.get', new=mock_requests_get)
    def test_service_sources_download(self):
        with ExonumClient(hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT,
                          private_api_port=EXONUM_PRIVATE_PORT) as client:
            client.load_main_proto_files()
            client.load_service_proto_files(0, 'exonum-supervisor:0.11.0')

            service_module = ModuleManager.import_service_module('exonum-supervisor:0.11.0', 'service')

    # TODO add more tests
