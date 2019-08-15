import unittest
import sys
import os

from exonum.module_manager import ModuleManager


class TestModuleManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Add folder with pre-compiled protobuf messages to the path (so it can be imported)
        sys.path.append(os.path.abspath('tests/proto_dir'))

    @classmethod
    def tearDownClass(self):
        # Remove protobuf directory from the path.
        sys.path.remove(os.path.abspath('tests/proto_dir'))

    def setUp(self):
        # Unload any previously loaded `exonum_main` modules from other tests
        loaded_modules = list(sys.modules.keys())
        for module in loaded_modules:
            if module.startswith('exonum_modules'):
                del sys.modules[module]

    def test_load_main(self):
        # Check that main module is loaded correctly
        main_module = ModuleManager.import_main_module('runtime')
        main_module.AnyTx()

    def test_load_fail_main(self):
        # Check that incorrect module import raises exception
        with self.assertRaises(ModuleNotFoundError):
            main_module = ModuleManager.import_main_module('no_module')

    def test_load_service(self):
        # Check that cryptocurrency service is loaded correctly
        cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')
        cryptocurrency_module.CreateWallet()

    def test_load_fail_service(self):
        # Check that incorrect module for correct service import raises exception
        cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
        with self.assertRaises(ModuleNotFoundError):
            ModuleManager.import_service_module(cryptocurrency_service_name, 'no_module')

        # Check that import module for incorrect service raises exception
        with self.assertRaises(ModuleNotFoundError):
            ModuleManager.import_service_module('no_service', 'service')
