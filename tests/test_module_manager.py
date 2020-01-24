# pylint: disable=missing-docstring, protected-access
# type: ignore

from exonum_client.crypto import Hash, PublicKey, PUBLIC_KEY_BYTES_LEN
from exonum_client.module_manager import ModuleManager
from exonum_client.message import MessageGenerator

from .module_user import PrecompiledModuleUserTestCase


class TestModuleManager(PrecompiledModuleUserTestCase):
    def test_load_main(self):
        # Check that the main module is loaded correctly:
        main_module = ModuleManager.import_main_module("runtime")
        main_module.AnyTx()

    def test_load_fail_main(self):
        # Check that an incorrect module import raises an exception:
        with self.assertRaises(ModuleNotFoundError):
            _main_module = ModuleManager.import_main_module("no_module")

    def test_load_service(self):
        # Check that the Cryptocurrency service is loaded correctly:
        cryptocurrency_service_name = "exonum-cryptocurrency-advanced"
        version = "0.11.0"
        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, version, "service")
        cryptocurrency_module.CreateWallet()

    def test_load_fail_service(self):
        # Check that import of an incorrect module for the correct service raises an exception:
        cryptocurrency_service_name = "exonum-cryptocurrency-advanced:0.11.0"
        version = "0.11.0"
        with self.assertRaises(ModuleNotFoundError):
            ModuleManager.import_service_module(cryptocurrency_service_name, version, "no_module")

        # Check that module import for an incorrect service raises an exception:
        with self.assertRaises(ModuleNotFoundError):
            ModuleManager.import_service_module("no_service", version, "service")

    def test_to_caller_address(self) -> None:
        """Tests converting PublicKey to caller address."""
        public_key = PublicKey(bytes([i for i in range(PUBLIC_KEY_BYTES_LEN)]))
        hash_address = MessageGenerator.pk_to_hash_address(public_key)
        self.assertEqual(hash_address.hex(), "fc608d4bd40aee124e73a8036d38db51788b79a18bb51d80ea15ca5fddaace69")
