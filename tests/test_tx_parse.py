import copy

import unittest
from pysodium import crypto_hash_sha256, crypto_sign_keypair
import sys
import os
# from tests.proto_test.timestamping_pb2 import TxTimestamp
# from tests.proto_test.helpers_pb2 import Hash, PublicKey
from exonum.message import ExonumMessage, MessageGenerator
from exonum.module_manager import ModuleManager

HASH_DATA = '1'
DATA_HASH = crypto_hash_sha256(HASH_DATA.encode())
SERVICE_ID = 130
MESSAGE_ID = 1

class TestTxParse(unittest.TestCase):
    def test_tx_success_parse(self):
        # Add folder with pre-compiled protobuf messages to the path (so it can be imported)
        sys.path.append(os.path.abspath('tests/proto_dir'))

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

        # Parse message
        parsed_message = ExonumMessage.from_hex(create_wallet_alice_tx.raw.hex(), cryptocurrency_service_name, 'CreateWallet')

        self.assertEqual(parsed_message.get_author(), keys[0])
        self.assertEqual(parsed_message.service_id, create_wallet_alice_tx.service_id)
        self.assertEqual(parsed_message.message_id, create_wallet_alice_tx.message_id)
        self.assertEqual(parsed_message.hash(), create_wallet_alice_tx.hash())

    def test_tx_fail_parse(self):
        # Add folder with pre-compiled protobuf messages to the path (so it can be imported)
        sys.path.append(os.path.abspath('tests/proto_dir'))

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

        # Parse message
        corrupted_message = '1a' + create_wallet_alice_tx.raw.hex()
        parsed_message = ExonumMessage.from_hex(corrupted_message, cryptocurrency_service_name, 'CreateWallet')

        self.assertIsNone(parsed_message)

    def test_tx_validation(self):
        # Add folder with pre-compiled protobuf messages to the path (so it can be imported)
        sys.path.append(os.path.abspath('tests/proto_dir'))

        # Gen init data
        keys = crypto_sign_keypair()
        fake_keys = crypto_sign_keypair()

        # Prepare original message
        cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')

        cryptocurrency_message_generator = MessageGenerator(1024, cryptocurrency_service_name)

        create_wallet_alice = cryptocurrency_module.CreateWallet()
        create_wallet_alice.name = 'Alice'

        # Create original message
        exonum_message = cryptocurrency_message_generator.create_message('CreateWallet', create_wallet_alice)
        exonum_message.sign(keys)

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
