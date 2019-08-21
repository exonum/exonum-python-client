import unittest

from exonum.list_proof import ProofParser, ListProof
from exonum.errors import MalformedProofError

Left = ListProof.Left
Right = ListProof.Right
Full = ListProof.Full
Leaf = ListProof.Leaf
Absent = ListProof.Absent


class TestProofParser(unittest.TestCase):
    def test_parse_simple(self):
        json_proof = {
            'left': {
                'val': '2dc17ca9c00d29ecff475d92f9b0c8885350d7b783e703b8ad21ae331d134496'
            },
            'right': 'c6f5873ab0f93c8be05e4e412cfc307fd98e58c9da9e6f582130882e672eb742'
        }

        proof_parser = ProofParser(bytes.fromhex)
        proof = proof_parser.parse(json_proof)

        expected_proof = Left(left=Leaf(val='2dc17ca9c00d29ecff475d92f9b0c8885350d7b783e703b8ad21ae331d134496'),
                              right='c6f5873ab0f93c8be05e4e412cfc307fd98e58c9da9e6f582130882e672eb742')

        self.assertEqual(proof, expected_proof)

        json_proof = {
            'left': '88e24b8560daa0fe0333b3e037e727bfa1bc9763af9b8f13bc9d430aea5d1e56',
            'right': {
                'val': 'c9d662f802867504736f7bb027408d00f118802dd4b9d904b456a1b5cc631c92'
            }
        }

        proof_parser = ProofParser(bytes.fromhex)
        proof = proof_parser.parse(json_proof)

        expected_proof = Right(left='88e24b8560daa0fe0333b3e037e727bfa1bc9763af9b8f13bc9d430aea5d1e56',
                               right=Leaf(val='c9d662f802867504736f7bb027408d00f118802dd4b9d904b456a1b5cc631c92'))

        self.assertEqual(proof, expected_proof)

    def test_parse_full(self):
        json_proof = {
            'left': {
                'val': '2dc17ca9c00d29ecff475d92f9b0c8885350d7b783e703b8ad21ae331d134496'
            },
            'right': {
                'val': 'c6f5873ab0f93c8be05e4e412cfc307fd98e58c9da9e6f582130882e672eb742'
            }
        }

        proof_parser = ProofParser(bytes.fromhex)
        proof = proof_parser.parse(json_proof)

        expected_proof = Full(left=Leaf(val='2dc17ca9c00d29ecff475d92f9b0c8885350d7b783e703b8ad21ae331d134496'),
                              right=Leaf(val='c6f5873ab0f93c8be05e4e412cfc307fd98e58c9da9e6f582130882e672eb742'))

        self.assertEqual(proof, expected_proof)

    def test_parse_absent(self):
        json_proof = {
            'length': 5,
            'hash': '5ba859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9'
        }

        proof_parser = ProofParser(bytes.fromhex)
        proof = proof_parser.parse(json_proof)

        expected_proof = Absent(length=5, hash='5ba859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9')

        self.assertEqual(proof, expected_proof)

    def test_parse_malformed_raises(self):
        malformed_proofs = [
            {
                'malformed': 'proof'
            },
            {
                'left': '1a',
                'right': {
                    'val': '5ba859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9'
                }
            },
            {
                'left': '5ba859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9',
                'right': '5ba859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9'
            },
            {
                'left': '5ba859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9',
                'right': {
                    'val': 'XXa859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9'
                }
            },
            {
                'length': '5',
                'hash': '5ba859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9'
            },
            {
                'length': 5,
                'hash': 'XXa859b4d1799cb27ece9db8f7a76a50fc713a5d9d22f753eca42172996a88f9'
            }
        ]

        proof_parser = ProofParser(bytes.fromhex)

        for malformed_proof in malformed_proofs:
            with self.assertRaises(MalformedProofError):
                proof = proof_parser.parse(malformed_proof)
