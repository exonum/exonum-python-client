import unittest

from exonum.proofs.map_proof import ProofPath, MapProof, KEY_SIZE


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
        full_tree = {
          "entries": [
            {
              "missing": {
                "tag": 3,
                "group_id": 1024,
                "index_id": 0
              }
            }
          ],
          "proof": [
            {
              "path": "0",
              "hash": "90c6641741113ce7cc75e5aeadeefdde21a123088e5b3650f6090117bbde543f"
            },
            {
              "path": "1011001101100100010001101010100001110010101101100110111001001101010011011001110101110100000011100000001101010011110000110011001110101111001011001001111111101101011100101010110100011101000110011001100000110111000010100000100111000001000010110101000000001010",
              "hash": "e229a42f60f34c1cfdd5bf8e2b77efe8a39b479c6acf711b80766c87b5cbde90"
            },
            {
              "path": "1011110000101000001000110111110110110011111111001111101001101111011010100101101100111000010111100110000110100011100100100011001010001111110000101010001101000010100011000011011101110100011100011101111011100001011101011000000010011001101100001000111000000010",
              "hash": "d705c7adc905020df57795a6f0c36e15f7442708761af06d0679203448ad888c"
            },
            {
              "path": "11",
              "hash": "f160a482bbd2ba5116906c30f02a55f5813a9799d23d0581e43a2c388b96d075"
            }
          ]
        }

        parsed_proof = MapProof.parse(full_tree)
        print(parsed_proof)
