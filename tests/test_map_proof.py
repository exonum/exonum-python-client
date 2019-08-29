import unittest

from exonum.proofs.map_proof import ProofPath, MapProof, KEY_SIZE


class TestProofPath(unittest.TestCase):
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

    def test_parse_path(self):
        path_str = '11001100'

        path = ProofPath.parse(path_str)

        data_bytes = bytearray([0] * KEY_SIZE)
        data_bytes[0] = 0b0011_0011
        expected_path = ProofPath.from_bytes(data_bytes)
        expected_path.set_end(8)

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
