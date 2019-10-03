import unittest

from exonum_client.crypto import Hash
from exonum_client.proofs.list_proof import ListProof
from exonum_client.proofs.list_proof.proof_parser import ProofParser
from exonum_client.proofs.list_proof.list_proof_element import ListProofElement
from exonum_client.proofs.list_proof.errors import MalformedListProofError, ListProofVerificationError

Left = ListProofElement.Left
Right = ListProofElement.Right
Full = ListProofElement.Full
Leaf = ListProofElement.Leaf
Absent = ListProofElement.Absent


def to_bytes(hex_data):
    return bytes.fromhex(hex_data)


class TestProofParser(unittest.TestCase):
    def setUp(self):
        self.HASH_A = "2dc17ca9c00d29ecff475d92f9b0c8885350d7b783e703b8ad21ae331d134496"
        self.HASH_B = "c6f5873ab0f93c8be05e4e412cfc307fd98e58c9da9e6f582130882e672eb742"
        self.HASH_A_BYTES = to_bytes(self.HASH_A)
        self.HASH_B_BYTES = to_bytes(self.HASH_B)

    def test_parse_simple(self):
        json_proof = {"left": {"val": self.HASH_A}, "right": self.HASH_B}

        proof_parser = ProofParser(bytes.fromhex)
        proof = proof_parser.parse(json_proof)

        expected_proof = Left(left=Leaf(val=self.HASH_A, val_raw=self.HASH_A_BYTES), right=self.HASH_B_BYTES)

        self.assertEqual(proof, expected_proof)

        json_proof = {"left": self.HASH_A, "right": {"val": self.HASH_B}}

        proof_parser = ProofParser(bytes.fromhex)
        proof = proof_parser.parse(json_proof)

        expected_proof = Right(left=self.HASH_A_BYTES, right=Leaf(val=self.HASH_B, val_raw=self.HASH_B_BYTES))

        self.assertEqual(proof, expected_proof)

    def test_parse_single_left(self):
        json_proof = {"left": {"val": self.HASH_A}}

        proof_parser = ProofParser(bytes.fromhex)
        proof = proof_parser.parse(json_proof)

        expected_proof = Left(left=Leaf(val=self.HASH_A, val_raw=self.HASH_A_BYTES), right=None)

        self.assertEqual(proof, expected_proof)

    def test_parse_full(self):
        json_proof = {"left": {"val": self.HASH_A}, "right": {"val": self.HASH_B}}

        proof_parser = ProofParser(bytes.fromhex)
        proof = proof_parser.parse(json_proof)

        expected_proof = Full(
            left=Leaf(val=self.HASH_A, val_raw=self.HASH_A_BYTES),
            right=Leaf(val=self.HASH_B, val_raw=self.HASH_B_BYTES),
        )

        self.assertEqual(proof, expected_proof)

    def test_parse_absent(self):
        json_proof = {"length": 5, "hash": self.HASH_A}

        proof_parser = ProofParser(bytes.fromhex)
        proof = proof_parser.parse(json_proof)

        expected_proof = Absent(length=5, hash=self.HASH_A_BYTES)

        self.assertEqual(proof, expected_proof)

    def test_parse_malformed_raises(self):
        malformed_proofs = [
            {"malformed": "proof"},
            {"left": "1a", "right": {"val": "5ba859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9"}},
            {
                "left": "5ba859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9",
                "right": "5ba859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9",
            },
            {
                "left": "5ba859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9",
                "right": {"val": "XXa859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9"},
            },
            {"length": "5", "hash": "5ba859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9"},
            {"length": 5, "hash": "XXa859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9"},
        ]

        proof_parser = ProofParser(bytes.fromhex)

        for malformed_proof in malformed_proofs:
            with self.assertRaises(MalformedListProofError):
                proof_parser.parse(malformed_proof)


class TestListProof(unittest.TestCase):
    def test_proof_simple(self):
        stored_val = "6b70d869aeed2fe090e708485d9f4b4676ae6984206cf05efc136d663610e5c9"
        proof_json = {
            "left": {"val": stored_val},
            "right": "eae60adeb5c681110eb5226a4ef95faa4f993c4a838d368b66f7c98501f2c8f9",
        }

        tx_count = 2
        expected_hash = Hash(bytes.fromhex("07df67b1a853551eb05470a03c9245483e5a3731b4b558e634908ff356b69857"))

        proof = ListProof.parse(proof_json)

        result = proof.validate(tx_count, expected_hash)

        self.assertEqual(result, [(0, stored_val)])

    def test_incorrect_proof_raises(self):
        # Test that incorrect proof verification will raise an error.

        stored_val = "6b70d869aeed2fe090e708485d9f4b4676ae6984206cf05efc136d663610e5c9"
        incorrect_proof_json = {
            "left": {"val": stored_val},
            "right": "ffe60adeb5c681110eb5226a4ef95faa4f993c4a838d368b66f7c98501f2c8f9",
        }

        tx_count = 2
        expected_hash = Hash(bytes.fromhex("07df67b1a853551eb05470a03c9245483e5a3731b4b558e634908ff356b69857"))

        proof = ListProof.parse(incorrect_proof_json)

        with self.assertRaises(ListProofVerificationError):
            result = proof.validate(tx_count, expected_hash)

        # Test that verification of proof against incorrect hash will raise an error.

        stored_val = "6b70d869aeed2fe090e708485d9f4b4676ae6984206cf05efc136d663610e5c9"
        proof_json = {
            "left": {"val": stored_val},
            "right": "eae60adeb5c681110eb5226a4ef95faa4f993c4a838d368b66f7c98501f2c8f9",
        }

        tx_count = 2
        incorrect_expected_hash = Hash(
            bytes.fromhex("ffdf67b1a853551eb05470a03c9245483e5a3731b4b558e634908ff356b69857")
        )

        proof = ListProof.parse(incorrect_proof_json)

        with self.assertRaises(ListProofVerificationError):
            result = proof.validate(tx_count, incorrect_expected_hash)

    def test_proof_range(self):
        proof_json = {
            "left": {
                "left": {
                    "left": {"val": "4507b25b6c91cbeba4320ac641728a92f4c085674e11c96b5a5830eddfe7a07a"},
                    "right": {"val": "17c18e8cfbba5cd179cb9067f28e5a6dc8aeb2a66a7cd7237746f891a2e125b7"},
                },
                "right": {
                    "left": {"val": "183c6af10407efd8ab875cdf372a5e5893e2527f77fec4bbbcf14f2dd5c22340"},
                    "right": {"val": "378ec583913aad58f857fa016fbe0b0fccede49454e9e4bd574e6234a620869f"},
                },
            },
            "right": {
                "left": {
                    "left": {"val": "8021361a8e6cd5fbd5edef78140117a0802b3dc187388037345b8b65835382b2"},
                    "right": {"val": "8d8b0adab49c2568c2b62ba0ab51ac2a6961b73c3f3bb1b596dd62a0a9971aac"},
                }
            },
        }

        tx_count = 6
        expected_hash = Hash(bytes.fromhex("3bb680f61d358cc208003e7b42f077402fdb05388dc0e7f3099551e4f86bb70a"))

        proof = ListProof.parse(proof_json)

        res = proof.validate(tx_count, expected_hash)

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
        expected_hash = Hash(bytes.fromhex("07df67b1a853551eb05470a03c9245483e5a3731b4b558e634908ff356b69857"))

        proof_json = {"length": tx_count, "hash": "34e927df0267eac2dbd7e27f0ad9de2b3dba7af7c1c84b9cab599b8048333c3b"}

        proof = ListProof.parse(proof_json)

        res = proof.validate(tx_count, expected_hash)

        self.assertEqual(res, [])
