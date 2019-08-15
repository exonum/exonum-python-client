import copy
import unittest
from pysodium import crypto_hash_sha256, crypto_sign_keypair
import sys
import os

from exonum.message import ExonumMessage, MessageGenerator
from exonum.module_manager import ModuleManager

class TestTxParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Add folder with pre-compiled protobuf messages to the path (so it can be imported)
        sys.path.append(os.path.abspath('tests/proto_dir'))

        # Unload any previously loaded `exonum_main` modules from test_exonum_client
        loaded_modules = list(sys.modules.keys())
        for module in loaded_modules:
            if module.startswith('exonum_modules'):
                del sys.modules[module]

        # Gen init data
        keys = crypto_sign_keypair()

        # Prepare original message
        cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'

        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')

        cryptocurrency_message_generator = MessageGenerator(1024, cryptocurrency_service_name)

        create_wallet_alice = cryptocurrency_module.CreateWallet()
        create_wallet_alice.name = 'Alice'

        # Create original message
        create_wallet_alice_tx = cryptocurrency_message_generator.create_message('CreateWallet', create_wallet_alice)
        create_wallet_alice_tx.sign(keys)

        cls.keys = keys
        cls.exonum_message = create_wallet_alice_tx
        cls.cryptocurrency_service_name = cryptocurrency_service_name

    @classmethod
    def tearDownClass(self):
        # Remove protobuf directory from the path.
        sys.path.remove(os.path.abspath('tests/proto_dir'))

    def test_tx_success_parse(self):
        exonum_message = self.exonum_message
        service_name = self.cryptocurrency_service_name
        
        # Parse message
        parsed_message = ExonumMessage.from_hex(exonum_message.raw.hex(), service_name, 'CreateWallet')

        self.assertEqual(parsed_message.get_author(), TestTxParse.keys[0])
        self.assertEqual(parsed_message.service_id, exonum_message.service_id)
        self.assertEqual(parsed_message.message_id, exonum_message.message_id)
        self.assertEqual(parsed_message.hash(), exonum_message.hash())

    def test_tx_fail_parse(self):
        exonum_message = self.exonum_message
        service_name = self.cryptocurrency_service_name

        # Parse message
        corrupted_message = '1a' + exonum_message.raw.hex()
        parsed_message = ExonumMessage.from_hex(corrupted_message, service_name, 'CreateWallet')

        self.assertIsNone(parsed_message)

    def test_tx_validation(self):
        exonum_message = self.exonum_message

        # Gen init data
        fake_keys = crypto_sign_keypair()

        # Checks that origin message validates right
        self.assertTrue(exonum_message.validate())

        # Check corrupted author message
        corrupt_message = copy.deepcopy(exonum_message)
        corrupt_message.author = fake_keys[0]
        self.assertFalse(corrupt_message.validate())

        # Check corrupted signature message
        corrupt_message = copy.deepcopy(exonum_message)
        sig = bytearray(corrupt_message.signature)
        sig[0] = sig[0] ^ 1
        corrupt_message.signature = bytes(sig)
        self.assertFalse(corrupt_message.validate())

        # Check corrupted payload message
        corrupt_message = copy.deepcopy(exonum_message)
        raw = bytearray(corrupt_message.raw)
        raw[0] = raw[0] ^ 1
        corrupt_message.raw = bytes(raw)
        self.assertFalse(corrupt_message.validate())
