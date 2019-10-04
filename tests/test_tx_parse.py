# pylint: disable=missing-docstring, protected-access
# type: ignore

import copy
import unittest
import sys
import os

from exonum_client.message import ExonumMessage, MessageGenerator
from exonum_client.crypto import KeyPair
from exonum_client.module_manager import ModuleManager


class TestTxParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Add a folder with the pre-compiled Protobuf messages to the path (so that it could be imported):
        sys.path.append(os.path.abspath("tests/proto_dir"))

        # Unload any previously loaded `exonum_main` modules from test_exonum_client:
        loaded_modules = list(sys.modules.keys())
        for module in loaded_modules:
            if module.startswith("exonum_modules"):
                del sys.modules[module]

        # Gen init data:
        keys = KeyPair.generate()

        # Prepare an original message:
        cryptocurrency_service_name = "exonum-cryptocurrency-advanced:0.11.0"

        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, "service")

        cryptocurrency_message_generator = MessageGenerator(1024, cryptocurrency_service_name)

        create_wallet_alice = cryptocurrency_module.CreateWallet()
        create_wallet_alice.name = "Alice"

        # Create an original message:
        create_wallet_alice_tx = cryptocurrency_message_generator.create_message(create_wallet_alice)
        create_wallet_alice_tx.sign(keys)

        cls.keys = keys
        cls.exonum_message = create_wallet_alice_tx
        cls.cryptocurrency_service_name = cryptocurrency_service_name

    @classmethod
    def tearDownClass(self):
        # Remove the Protobuf directory from the path:
        sys.path.remove(os.path.abspath("tests/proto_dir"))

    def test_tx_success_parse(self):
        exonum_message = self.exonum_message
        service_name = self.cryptocurrency_service_name

        # Parse the message:
        parsed_message = ExonumMessage.from_hex(exonum_message.signed_raw().hex(), service_name, "CreateWallet")

        self.assertEqual(parsed_message.author(), TestTxParse.keys.public_key)
        self.assertEqual(parsed_message._instance_id, exonum_message._instance_id)
        self.assertEqual(parsed_message._message_id, exonum_message._message_id)
        self.assertEqual(parsed_message.hash(), exonum_message.hash())

    def test_tx_fail_parse(self):
        exonum_message = self.exonum_message
        service_name = self.cryptocurrency_service_name

        # Parse the message:
        corrupted_message = "1a" + exonum_message.signed_raw().hex()
        parsed_message = ExonumMessage.from_hex(corrupted_message, service_name, "CreateWallet")

        self.assertIsNone(parsed_message)

    def test_tx_validation(self):
        exonum_message = self.exonum_message

        # Gen init data:
        fake_keys = KeyPair.generate()

        # Check that validation of the original message passes successfully:
        self.assertTrue(exonum_message.validate())

        # Check a corrupted author message:
        corrupt_message = copy.deepcopy(exonum_message)
        corrupt_message._author = fake_keys.public_key
        self.assertFalse(corrupt_message.validate())

        # Check a corrupted signature message:
        corrupt_message = copy.deepcopy(exonum_message)
        sig = bytearray(corrupt_message._signature.value)
        sig[0] = sig[0] ^ 1
        corrupt_message._signature.value = bytes(sig)
        self.assertFalse(corrupt_message.validate())

        # Check a corrupted payload message:
        corrupt_message = copy.deepcopy(exonum_message)
        raw = bytearray(corrupt_message._signed_tx_raw)
        raw[0] = raw[0] ^ 1
        corrupt_message._signed_tx_raw = bytes(raw)
        self.assertFalse(corrupt_message.validate())
