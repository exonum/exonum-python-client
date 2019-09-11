import unittest
import random

from exonum.proofs.encoder import build_encoder_function
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
            (ProofPath.from_bytes(bytes([1] * 32)), ProofPath.from_bytes(bytes([1] * 32)).prefix(254)),
            (ProofPath.from_bytes(bytes([1] * 32)).prefix(10), ProofPath.from_bytes(bytes([2] * 32)).prefix(10)),
            (ProofPath.from_bytes(bytes([1] * 32)).prefix(11), ProofPath.from_bytes(bytes([2] * 32)).prefix(10)),
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

    def test_match_len(self):
        def _common_prefix_len(a, b):
            max_length = min(len(a), len(b))
            for i in range(max_length):
                if a[i] != b[i]:
                    return i
            return max_length

        def _generate_number(min_length=1):
            max_length = 256

            length = random.randint(min_length, max_length)

            seq = ''.join([random.choice(['0', '1']) for _ in range(length)])

            return seq

        def _generate_sample(min_length=1):
            left = _generate_number(min_length)
            right = _generate_number(min_length)
            common_length = _common_prefix_len(left, right)

            return (left, right, common_length)

        random.seed(1234)

        test_data = [
            ('11110000', '11110000', 8),
            ('11110000', '11110001', 7),
            ('11110000', '1111000', 7),
            ('1111000', '11110000', 7),
            ('11111111', '11110000', 4),
            ('11111111', '01110000', 0),
            ('11111111', '11100000', 3),
            ('11111111', '111', 3),
        ]

        test_data += [_generate_sample() for _ in range(20)]
        test_data += [_generate_sample(min_length=256) for _ in range(20)]

        for first, second, expected_match_len in test_data:
            first_path = ProofPath.parse(first)
            second_path = ProofPath.parse(second)

            self.assertEqual(first_path.match_len(second_path, 0), expected_match_len)
            self.assertEqual(second_path.match_len(first_path, 0), expected_match_len, f"{second_path}, {first_path}")

            if len(first_path) > 2 and len(second_path) > 2 and expected_match_len > 2:
                self.assertEqual(first_path.match_len(second_path, 2), expected_match_len)
                self.assertEqual(second_path.match_len(first_path, 2), expected_match_len)

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

        cryptocurrency_decoder = build_encoder_function(cryptocurrency_module.Wallet)

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
                 "key": "1dddbac5d8f16ef97b20a6abe854f6356436ce97b71d9d439b17b91f3a144ac6",
                 "value": {
                    "pub_key": {
                       "data": list(bytes.fromhex("1dddbac5d8f16ef97b20a6abe854f6356436ce97b71d9d439b17b91f3a144ac6"))
                    },
                    "name": "Alice1",
                    "balance": 95,
                    "history_len": 6,
                    "history_hash": {
                       "data": list(bytes.fromhex("1ff3a775f6df930ad63c5f1ce683393c7f080dbd5ca544e40c7488640bf732f8"))
                    }
                 }
              }
           ],
           "proof": [
              {
                 "path": "011000000110111110010010010111010111010101111110110101111001110111011111101001111001100000010"
                         "111001110000111111000111111111100000011011000100001111101001011000100000110110001101000000000"
                         "1010000101111100110000011111011100111110010101101110000100010110010001",
                 "hash": "deaa44743a85249302a4633d8cdde96526064c56715318fa0712fe4befb1fef3"
              }
           ]
        }

        cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')

        cryptocurrency_decoder = build_encoder_function(cryptocurrency_module.Wallet)

        parsed_proof = MapProof.parse(proof, lambda x: bytes.fromhex(x), cryptocurrency_decoder)

        result = parsed_proof.check()

        entries = result.all_entries()

        self.assertEqual(len(entries), 1)
        self.assertFalse(entries[0].is_missing)
        self.assertEqual(entries[0].key, proof['entries'][0]['key'])
        self.assertEqual(entries[0].value, proof['entries'][0]['value'])

        expected_hash = '7adcdfe51855dc073681b7f9274a414d4d9f378e94e02c39e04819c6f9ed27e7'

        self.assertEqual(result.root_hash().hex(), expected_hash)

    def test_map_proof_validate_several_proof_entries(self):
        proof = {
          "entries": [
            {
              "key": {
                "tag": 3,
                "group_id": 1024,
                "index_id": 0
              },
              "value": "d24f95722fb68800b586148232953a1453a5b8dee7af2d213d96e5ce63516380"
            }
          ],
          "proof": [
            {
              "path": "0",
              "hash": "9e39ec70d792124cc0039d5b25ca8a00c7e26e7063994deb01ca940aa9e68128"
            },
            {
              "path": "101100110110010001000110101010000111001010110110011011100100110101001101100111010111010000001110"
                      "000000110101001111000011001100111010111100101100100111111110110101110010101011010001110100011001"
                      "1001100000110111000010100000100111000001000010110101000000001010",
              "hash": "23e07283aafec41b627fef86d058517fbf820c50b05ec683fcf2b1504605ad87"
            },
            {
              "path": "101111000010100000100011011111011011001111111100111110100110111101101010010110110011100001011110"
                      "011000011010001110010010001100101000111111000010101000110100001010001100001101110111010001110001"
                      "1101111011100001011101011000000010011001101100001000111000000010",
              "hash": "3fe2e4c293ecc21180c2aaaeec88adf5fe8e5371ef26466d76c7fbc6ab1d416a"
            },
            {
              "path": "11",
              "hash": "96f00895570f12ef4b0294d3cc667fcbb3b235197ac11abca280c1be2922ca31"
            }
          ]
        }

        def key_encoder(data):
            import struct
            format_str = '>HIH'
            res = struct.pack(format_str, data['tag'], data['group_id'], data['index_id'])
            return res

        def value_encoder(data):
            return bytes.fromhex(data)

        parsed_proof = MapProof.parse(proof, key_encoder, value_encoder)

        result = parsed_proof.check()

        entries = result.all_entries()
        self.assertEqual(len(entries), 1)
        self.assertFalse(entries[0].is_missing)
        self.assertEqual(entries[0].key, proof['entries'][0]['key'])
        self.assertEqual(entries[0].value, proof['entries'][0]['value'])

        expected_hash = '3ccac1646fbbbc7e22a70b2a426c0d22bdde14a03f4ffc3547207245a4774afc'

        self.assertEqual(result.root_hash().hex(), expected_hash)
