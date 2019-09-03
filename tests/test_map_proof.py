import unittest

from exonum.proofs.map_proof import MapProof
from exonum.proofs.map_proof.proof_path import ProofPath
from exonum.proofs.map_proof.constants import KEY_SIZE
from exonum.proofs.map_proof.map_proof_builder import MapProofBuilder
from exonum.module_manager import ModuleManager

from .module_user import PrecompiledModuleUserTestCase


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

        self.assertEqual(len(parsed_proof.entries), 1)
        self.assertEqual(parsed_proof.entries[0].key, full_tree['entries'][0]['missing'])

        self.assertEqual(len(parsed_proof.proof), len(full_tree['proof']))


class TestMapProof(PrecompiledModuleUserTestCase):
    def test_map_proof_validate_empty_proof(self):
        proof = {
          "entries": [],
          "proof": []
        }

        cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')

        cryptocurrency_decoder = MapProofBuilder.build_encoder_function(cryptocurrency_module.Wallet)

        parsed_proof = MapProof.parse(proof, lambda x: bytes.fromhex(x), cryptocurrency_decoder)

        result = parsed_proof.check()

        entries = result.all_entries()

        self.assertEqual(len(entries), 0)

        expected_hash = '7324b5c72b51bb5d4c180f1109cfd347b60473882145841c39f3e584576296f9'

        self.assertEqual(result.root_hash().hex(), expected_hash)

    def test_map_proof_validate_one_node(self):
        proof = {
          "entries": [
            {
              "key": "d457386c836408ce3315a20924b13e1282905e78557b7e1933a66d42f33317cb",
              "value": {
                "pub_key": {
                  "data": list(bytes.fromhex("d457386c836408ce3315a20924b13e1282905e78557b7e1933a66d42f33317cb"))
                },
                "name": "Alice1",
                "balance": 100,
                "history_len": 1,
                "history_hash": {
                  "data": list(bytes.fromhex("687ebb7ecacf4c1cc18394580922a6d9eae8aa54a1f8f044538a9d10fdae78b0"))
                }
              }
            }
          ],
          "proof": []
        }

        cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')

        cryptocurrency_decoder = MapProofBuilder.build_encoder_function(cryptocurrency_module.Wallet)

        parsed_proof = MapProof.parse(proof, lambda x: bytes.fromhex(x), cryptocurrency_decoder)

        result = parsed_proof.check()

        entries = result.all_entries()

        self.assertEqual(len(entries), 1)
        self.assertFalse(entries[0].is_missing)
        self.assertEqual(entries[0].key, proof['entries'][0]['key'])
        self.assertEqual(entries[0].value, proof['entries'][0]['value'])

        expected_hash = 'd034fa0456f92501fbb4750b483f8dd767c1a886f72f9ea0b268daec8808a6b5'

        self.assertEqual(result.root_hash().hex(), expected_hash)

    def test_map_proof_validate(self):
        proof = {
          "entries": [
            {
              "key": "e610db75b0bbbd4c606c4f8ca3fca9f916e9c8ae9a93b5b767082172454344b3",
              "value": {
                "pub_key": {
                  "data": list(bytes.fromhex("e610db75b0bbbd4c606c4f8ca3fca9f916e9c8ae9a93b5b767082172454344b3"))
                },
                "name": "Alice1",
                "balance": 95,
                "history_len": 6,
                "history_hash": {
                  "data": list(bytes.fromhex("19faf859d7456907c76f085af5b7a2d7621d992617a349006c07720957d5d49d"))
                }
              }
            }
          ],
          "proof": [
            {
              "path": "010000100100100010100100110001100111011011011000010011011011111111110110001101001001011010111100"
                      "001010010011011010001110011001011001010101100100000101010010000001101011100000010011101101001011"
                      "1110010011011011101001110000111111000000011111100010001011010000",
              "hash": "dbeab4aa952e2c2cb3dc921aa42c9b508e2e5961cad2463f7203d228abc204c8"
            }
          ]
        }

        cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')

        cryptocurrency_decoder = MapProofBuilder.build_encoder_function(cryptocurrency_module.Wallet)

        parsed_proof = MapProof.parse(proof, lambda x: bytes.fromhex(x), cryptocurrency_decoder)

        result = parsed_proof.check()

        entries = result.all_entries()
        self.assertEqual(len(entries), 1)
        self.assertFalse(entries[0].is_missing)
        self.assertEqual(entries[0].key, proof['entries'][0]['key'])
        self.assertEqual(entries[0].value, proof['entries'][0]['value'])

        expected_hash = '27d89236d79d59bfdc135669aeb4608afa644edc06469d93147ef85852e275e2'

        self.assertEqual(result.root_hash().hex(), expected_hash)

    def test_map_proof_validate_several_entries(self):
        proof = {
          "entries": [
            {
              "key": "7fef155e2ede14d8cceba3e740fd0615a1c41de9a28aa042236ccc159788e1ba",
              "value": {
                "pub_key": {
                  "data": list(bytes.fromhex("7fef155e2ede14d8cceba3e740fd0615a1c41de9a28aa042236ccc159788e1ba"))
                },
                "name": "Bob3",
                "balance": 100,
                "history_len": 1,
                "history_hash": {
                  "data": list(bytes.fromhex("e50f400d911c340a852d822b3d2fbc5a99514f62964bf519033486abd29966de"))
                }
              }
            }
          ],
          "proof": [
            {
              "path": "0",
              "hash": "6cfabb13b5ee5a6cb6ba7b99c12f2799b4d3a539fa3feb3eaefdc1de20312292"
            },
            {
              "path": "110010101000101110100110110110101001011000110110101011010111010101010100111101100101101111010110"
                      "100000010101101011100100101111101101001001010111100111101011000010100000100110111101010100100111"
                      "1111110010011011001110011000101010100010101011011010101100000011",
              "hash": "07ad84744967809ce2f412d1bd5fa65249e1cbef2022a21b3885b51012eea71f"
            },
            {
              "path": "111101010000000111101100001110100000111100100111111000000010101011010001000001010111001010000110"
                      "110101110111110101101100100110001101000011010100100100001111010001000110011101010110101101101000"
                      "0001001111001101010001111011001011001000110010100000110000101010",
              "hash": "759398ddf66effc9267ac0d2386193aa58705a96f709d47b2e3d378061dea9ff"
            }
          ]
        }

        cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')

        cryptocurrency_decoder = MapProofBuilder.build_encoder_function(cryptocurrency_module.Wallet)

        parsed_proof = MapProof.parse(proof, lambda x: bytes.fromhex(x), cryptocurrency_decoder)

        result = parsed_proof.check()

        entries = result.all_entries()
        self.assertEqual(len(entries), 1)
        self.assertFalse(entries[0].is_missing)
        self.assertEqual(entries[0].key, proof['entries'][0]['key'])
        self.assertEqual(entries[0].value, proof['entries'][0]['value'])

        expected_hash = '22ea6ced5c4ab54c4f2c6317f1bba8ea7a67891d04e58bfd9baa0670f7933050'

        self.assertEqual(result.root_hash().hex(), expected_hash)
