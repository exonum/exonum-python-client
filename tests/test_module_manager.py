import unittest
import sys
import os

from exonum.module_manager import ModuleManager

from .module_user import PrecompiledModuleUserTestCase


class TestModuleManager(PrecompiledModuleUserTestCase):
    def test_load_main(self):
        # Check that the main module is loaded correctly:
        main_module = ModuleManager.import_main_module("runtime")
        main_module.AnyTx()

    def test_load_fail_main(self):
        # Check that an incorrect module import raises an exception:
        with self.assertRaises(ModuleNotFoundError):
            main_module = ModuleManager.import_main_module("no_module")

    def test_load_service(self):
        # Check that the Cryptocurrency service is loaded correctly:
        cryptocurrency_service_name = "exonum-cryptocurrency-advanced:0.11.0"
        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, "service")
        cryptocurrency_module.CreateWallet()

    def test_load_fail_service(self):
        # Check that import of an incorrect module for the correct service raises an exception:
        cryptocurrency_service_name = "exonum-cryptocurrency-advanced:0.11.0"
        with self.assertRaises(ModuleNotFoundError):
            ModuleManager.import_service_module(cryptocurrency_service_name, "no_module")

        # Check that module import for an incorrect service raises an exception:
        with self.assertRaises(ModuleNotFoundError):
            ModuleManager.import_service_module("no_service", "service")
