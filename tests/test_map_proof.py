import unittest
import sys
import os

from exonum.proofs.map_proof import MapProof
from exonum.proofs.map_proof.proof_path import ProofPath
from exonum.proofs.map_proof.constants import KEY_SIZE
from exonum.proofs.map_proof.map_proof_builder import MapProofBuilder
from exonum.module_manager import ModuleManager


class TestProofPath(unittest.TestCase):
    def test_basic_methods(self):
        # By default path is leaf.
        data_bytes = bytearray([0] * KEY_SIZE)
        data_bytes[0] = 0b0011_0011
        path = ProofPath.from_bytes(data_bytes)

        self.assertTrue(path.is_leaf())
        self.assertEqual(path.start(), 0)
        self.assertEqual(path.end(), 256)

        # Make it branch.
        path.set_end(8)

        self.assertFalse(path.is_leaf())
        self.assertEqual(path.start(), 0)
        self.assertEqual(path.end(), 8)

        # Make it leaf back.
        path.set_end(None)

        self.assertTrue(path.is_leaf())
        self.assertEqual(path.start(), 0)
        self.assertEqual(path.end(), 256)

    def test_eq(self):
        data_bytes = bytearray([0] * KEY_SIZE)
        data_bytes[0] = 0b0011_0011
        path_a = ProofPath.from_bytes(data_bytes)
        path_b = ProofPath.from_bytes(data_bytes)

        self.assertEqual(path_a, path_b)

        data_bytes = bytearray([0] * KEY_SIZE)
        data_bytes[0] = 0b1111_1111
        path_c = ProofPath.from_bytes(data_bytes)

        self.assertNotEqual(path_a, path_c)

    def test_comparison(self):
        datasets = [
            (ProofPath.from_bytes(bytes([1] * 32)), ProofPath.from_bytes(bytes([254] * 32))),
            (ProofPath.from_bytes(bytes([0b0001_0001] * 32)), ProofPath.from_bytes(bytes([0b0010_0001] * 32))),
            (ProofPath.from_bytes(bytes([1] * 32)), ProofPath.from_bytes(bytes([1] * 32)).prefix(254))
        ]

        for path_a, path_b in datasets:
            self.assertTrue(path_a > path_b)
            self.assertTrue(path_b < path_a)
            self.assertFalse(path_a < path_b)
            self.assertFalse(path_b > path_a)

    def test_starts_with(self):
        data_bytes = bytearray([0] * KEY_SIZE)
        data_bytes[0] = 0b0011_0011
        path_a = ProofPath.from_bytes(data_bytes)
        path_b = ProofPath.from_bytes(data_bytes)

        path_b.set_end(8)

        # Support methods for 'starts_with'.
        self.assertEqual(path_a.match_len(path_b, 0), 8)
        self.assertEqual(path_a.common_prefix_len(path_b), 8)

        self.assertTrue(path_a.starts_with(path_b))
        self.assertFalse(path_b.starts_with(path_a))

    def test_prefix(self):
        data_bytes = bytearray([0] * KEY_SIZE)
        data_bytes[0] = 0b0011_0011
        path_a = ProofPath.from_bytes(data_bytes)

        path_b = ProofPath.from_bytes(data_bytes)
        path_b.set_end(8)

        path_c = path_a.prefix(8)

        self.assertEqual(path_b, path_c)

    def test_parse_path(self):
        path_strs = [
            # 1 byte
            '11001100',
            # 1.5 bytes
            '111111001100',
            # 255 symbols
            '101100110110010001000110101010000111001010110110011011100100110101001'
            '101100111010111010000001110000000110101001111000011001100111010111100'
            '101100100111111110110101110010101011010001110100011001100110000011011'
            '100001010000010011100000100001011010100000000101',
            # 256 symbols (full path).
            '101100110110010001000110101010000111001010110110011011100100110101001'
            '101100111010111010000001110000000110101001111000011001100111010111100'
            '101100100111111110110101110010101011010001110100011001100110000011011'
            '1000010100000100111000001000010110101000000001010'
        ]

        for path_str in path_strs:
            # Parse proof path.
            path = ProofPath.parse(path_str)

            # Convert string to path manually.
            byte_strs = [path_str[i:i+8] for i in range(0, len(path_str), 8)]
            path_bytes = [int(byte_str[::-1], 2) for byte_str in byte_strs]

            data_bytes = bytearray([0] * KEY_SIZE)
            data_bytes[:len(path_bytes)] = path_bytes[:]

            expected_path = ProofPath.from_bytes(data_bytes)

            # If path is not full, create prefix.
            if len(path_str) < 256:
                expected_path = expected_path.prefix(len(path_str))

            self.assertEqual(path, expected_path)


class TestMapProofParse(unittest.TestCase):
    def test_parse_full_tree(self):
        def mock_converter(val):
            return bytes()

        full_tree = {
          'entries': [
            {
              'missing': {
                'tag': 3,
                'group_id': 1024,
                'index_id': 0
              }
            }
          ],
          'proof': [
            {
              'path': '0',
              'hash': '90c6641741113ce7cc75e5aeadeefdde21a123088e5b3650f6090117bbde543f'
            },
            {
              'path': '101100110110010001000110101010000111001010110110011011100100110101001101100111010111010000001110'
                      '000000110101001111000011001100111010111100101100100111111110110101110010101011010001110100011001'
                      '1001100000110111000010100000100111000001000010110101000000001010',
              'hash': 'e229a42f60f34c1cfdd5bf8e2b77efe8a39b479c6acf711b80766c87b5cbde90'
            },
            {
              'path': '101111000010100000100011011111011011001111111100111110100110111101101010010110110011100001011110'
                      '011000011010001110010010001100101000111111000010101000110100001010001100001101110111010001110001'
                      '1101111011100001011101011000000010011001101100001000111000000010',
              'hash': 'd705c7adc905020df57795a6f0c36e15f7442708761af06d0679203448ad888c'
            },
            {
              'path': '11',
              'hash': 'f160a482bbd2ba5116906c30f02a55f5813a9799d23d0581e43a2c388b96d075'
            }
          ]
        }

        parsed_proof = MapProof.parse(full_tree, mock_converter, mock_converter)
        print(parsed_proof)


class TestMapProof(unittest.TestCase):
    def test_map_proof_validate(self):
        # TODO workaround because of the protobuf bug
        import base64
        data_raw = bytes([230, 16, 219, 117, 176, 187, 189, 76, 96, 108, 79, 140, 163, 252, 169, 249, 22, 233, 200, 174, 154, 147, 181, 183, 103, 8, 33, 114, 69, 67, 68, 179])
        data_b64 = str(base64.b64encode(data_raw), 'utf-8')

        history_hash_raw = bytes([25, 250, 248, 89, 215, 69, 105, 7, 199, 111, 8, 90, 245, 183, 162, 215, 98, 29, 153, 38, 23, 163, 73, 0, 108, 7, 114, 9, 87, 213, 212, 157])
        history_hash_b64 = str(base64.b64encode(history_hash_raw), 'utf-8')

        proof = {
          "entries": [
            {
              "key": "e610db75b0bbbd4c606c4f8ca3fca9f916e9c8ae9a93b5b767082172454344b3",
              "value": {
                "pub_key": {
                  "data": data_b64
                },
                "name": "Alice1",
                "balance": 95,
                "history_len": 6,
                "history_hash": {
                  "data": history_hash_b64
                }
              }
            }
          ],
          "proof": [
            {
              "path": "0100001001001000101001001100011001110110110110000100110110111111111101100011010010010110101111000010100100110110100011100110010110010101011001000001010100100000011010111000000100111011010010111110010011011011101001110000111111000000011111100010001011010000",
              "hash": "dbeab4aa952e2c2cb3dc921aa42c9b508e2e5961cad2463f7203d228abc204c8"
            }
          ]
        }

        # TODO move in setup?
        sys.path.append(os.path.abspath('tests/proto_dir'))
        cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')

        cryptocurrency_decoder = MapProofBuilder.build_encoder_function(cryptocurrency_module.Wallet)

        parsed_proof = MapProof.parse(proof, lambda x: bytes.fromhex(x), cryptocurrency_decoder)

        result = parsed_proof.check()

        print(result._entries)
        print(result._root_hash.hex())

        expected_hash = '27d89236d79d59bfdc135669aeb4608afa644edc06469d93147ef85852e275e2'

        print("EXPECTED HASH: {}".format(expected_hash))
