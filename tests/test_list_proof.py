import unittest

from exonum.proofs.list_proof import ListProof
from exonum.proofs.list_proof.key import ProofListKey
from exonum.proofs.list_proof.list_proof import HashedEntry
from exonum.proofs.list_proof.errors import MalformedListProofError, ListProofVerificationError
from exonum.proofs.hasher import Hasher


def to_bytes(hex_data):
    return bytes.fromhex(hex_data)


class TestListProofParse(unittest.TestCase):
    def setUp(self):
        self.HASH_A = "2dc17ca9c00d29ecff475d92f9b0c8885350d7b783e703b8ad21ae331d134496"
        self.HASH_B = "c6f5873ab0f93c8be05e4e412cfc307fd98e58c9da9e6f582130882e672eb742"
        self.HASH_A_BYTES = to_bytes(self.HASH_A)
        self.HASH_B_BYTES = to_bytes(self.HASH_B)

    def test_parse_hashed_entry(self):
        entry_json = {"index": 0, "height": 0, "hash": self.HASH_A}

        entry = HashedEntry.parse(entry_json)

        self.assertEqual(entry, HashedEntry(ProofListKey(0, 0), self.HASH_A_BYTES))

        malformed_entries = [
            {"index": 0, "hash": self.HASH_A},
            {"height": 0, "hash": self.HASH_A},
            {"index": 0, "height": 0},
            {"index": "abc", "height": 0, "hash": self.HASH_A},
            {"index": 0, "height": "cde", "hash": self.HASH_A},
            {"index": 0, "height": 0, "hash": 123},
        ]

        for malformed_entry in malformed_entries:
            with self.assertRaises(MalformedListProofError):
                HashedEntry.parse(malformed_entry)

    def test_parse_proof(self):
        json_proof = {"proof": [], "entries": [], "length": 0}

        proof = ListProof.parse(json_proof, to_bytes)

        self.assertEqual(proof._proof, [])
        self.assertEqual(proof._entries, [])
        self.assertEqual(proof._length, 0)
        self.assertEqual(proof._value_to_bytes, to_bytes)

        json_proof = {
            "proof": [{"index": 1, "height": 1, "hash": self.HASH_A}],
            "entries": [[0, self.HASH_B]],
            "length": 2,
        }

        proof = ListProof.parse(json_proof, to_bytes)

        self.assertEqual(proof._proof, [HashedEntry(ProofListKey(1, 1), self.HASH_A_BYTES)])
        self.assertEqual(proof._entries, [(0, self.HASH_B)])
        self.assertEqual(proof._length, 2)
        self.assertEqual(proof._value_to_bytes, to_bytes)

    def test_parse_malformed_raises(self):
        malformed_proofs = [
            {"malformed": "proof"},
            {"proof": [], "length": 0},
            {"entries": [], "length": 0},
            {"proof": [], "entries": []},
            {"proof": [123], "entries": [], "length": 0},
            {"proof": [], "entries": [123], "length": 0},
        ]

        for malformed_proof in malformed_proofs:
            with self.assertRaises(MalformedListProofError):
                ListProof.parse(malformed_proof, to_bytes)


class TestListProof(unittest.TestCase):
    def test_proof_simple(self):
        stored_val = "6b70d869aeed2fe090e708485d9f4b4676ae6984206cf05efc136d663610e5c9"
        proof_json = {
            "proof": [
                {"index": 1, "height": 1, "hash": "eae60adeb5c681110eb5226a4ef95faa4f993c4a838d368b66f7c98501f2c8f9"}
            ],
            "entries": [[0, "6b70d869aeed2fe090e708485d9f4b4676ae6984206cf05efc136d663610e5c9"]],
            "length": 2,
        }

        tx_count = 2
        expected_hash = "07df67b1a853551eb05470a03c9245483e5a3731b4b558e634908ff356b69857"

        proof = ListProof.parse(proof_json)

        result = proof.validate(to_bytes(expected_hash))

        self.assertEqual(result, [(0, stored_val)])

    def test_incorrect_proof_raises(self):
        # Test that incorrect proof verification will raise an error.

        stored_val = "6b70d869aeed2fe090e708485d9f4b4676ae6984206cf05efc136d663610e5c9"
        incorrect_proof_json = {
            "proof": [
                {"index": 1, "height": 1, "hash": "eae60adeb5c681110eb5226a4ef95faa4f993c4a838d368b66f7c98501f2c8f9"}
            ],
            "entries": [[0, "DEADBEEFaeed2fe090e708485d9f4b4676ae6984206cf05efc136d663610e5c9"]],
            "length": 2,
        }

        tx_count = 2
        expected_hash = "07df67b1a853551eb05470a03c9245483e5a3731b4b558e634908ff356b69857"

        proof = ListProof.parse(incorrect_proof_json)

        with self.assertRaises(ListProofVerificationError):
            result = proof.validate(to_bytes(expected_hash))

        # Test that verification of proof against incorrect hash will raise an error.

        stored_val = "6b70d869aeed2fe090e708485d9f4b4676ae6984206cf05efc136d663610e5c9"
        proof_json = {
            "proof": [
                {"index": 1, "height": 1, "hash": "eae60adeb5c681110eb5226a4ef95faa4f993c4a838d368b66f7c98501f2c8f9"}
            ],
            "entries": [[0, "6b70d869aeed2fe090e708485d9f4b4676ae6984206cf05efc136d663610e5c9"]],
            "length": 2,
        }

        tx_count = 2
        incorrect_expected_hash = "DEADBEEFa853551eb05470a03c9245483e5a3731b4b558e634908ff356b69857"

        proof = ListProof.parse(proof_json)

        with self.assertRaises(ListProofVerificationError):
            result = proof.validate(to_bytes(incorrect_expected_hash))

    def test_proof_range(self):
        proof_json = proof_json = {
            "proof": [],
            "entries": [
                [0, "4507b25b6c91cbeba4320ac641728a92f4c085674e11c96b5a5830eddfe7a07a"],
                [1, "17c18e8cfbba5cd179cb9067f28e5a6dc8aeb2a66a7cd7237746f891a2e125b7"],
                [2, "183c6af10407efd8ab875cdf372a5e5893e2527f77fec4bbbcf14f2dd5c22340"],
                [3, "378ec583913aad58f857fa016fbe0b0fccede49454e9e4bd574e6234a620869f"],
                [4, "8021361a8e6cd5fbd5edef78140117a0802b3dc187388037345b8b65835382b2"],
                [5, "8d8b0adab49c2568c2b62ba0ab51ac2a6961b73c3f3bb1b596dd62a0a9971aac"],
            ],
            "length": 6,
        }

        tx_count = 6
        expected_hash = "3bb680f61d358cc208003e7b42f077402fdb05388dc0e7f3099551e4f86bb70a"

        proof = ListProof.parse(proof_json)

        res = proof.validate(to_bytes(expected_hash))

        self.assertEqual(
            res,
            [
                (0, "4507b25b6c91cbeba4320ac641728a92f4c085674e11c96b5a5830eddfe7a07a"),
                (1, "17c18e8cfbba5cd179cb9067f28e5a6dc8aeb2a66a7cd7237746f891a2e125b7"),
                (2, "183c6af10407efd8ab875cdf372a5e5893e2527f77fec4bbbcf14f2dd5c22340"),
                (3, "378ec583913aad58f857fa016fbe0b0fccede49454e9e4bd574e6234a620869f"),
                (4, "8021361a8e6cd5fbd5edef78140117a0802b3dc187388037345b8b65835382b2"),
                (5, "8d8b0adab49c2568c2b62ba0ab51ac2a6961b73c3f3bb1b596dd62a0a9971aac"),
            ],
        )

    def test_proof_of_absence(self):
        tx_count = 2
        expected_hash = "07df67b1a853551eb05470a03c9245483e5a3731b4b558e634908ff356b69857"

        proof_json = {
            "proof": [
                {"index": 0, "height": 2, "hash": "34e927df0267eac2dbd7e27f0ad9de2b3dba7af7c1c84b9cab599b8048333c3b"}
            ],
            "entries": [],
            "length": 2,
        }

        proof = ListProof.parse(proof_json)

        res = proof.validate(to_bytes(expected_hash))

        self.assertEqual(res, [])
