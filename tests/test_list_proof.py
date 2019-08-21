import unittest

from exonum.list_proof import ProofParser, ListProof


class TestProofParser(unittest.TestCase):
    def test_parse_simple(self):
        json_proof = {
            'left': {
                'val': '2dc17ca9c00d29ecff475d92f9b0c8885350d7b783e703b8ad21ae331d134496'
            },
            'right': 'c6f5873ab0f93c8be05e4e412cfc307fd98e58c9da9e6f582130882e672eb742'
        }

        proof = ProofParser.parse(json_proof)

        print(proof)
