import collections
import struct
from enum import IntEnum
from pysodium import crypto_hash_sha256

from .errors import MalformedProofError


def is_dict(json):
    return isinstance(json, dict)


def is_field_dict(json, field):
    return isinstance(json.get(field), dict)


def is_field_hash(json, field):
    try:
        field = json.get(field)
        return isinstance(field, str) and len(field) == 64 and int(field, 16)
    except ValueError:
        return False


def is_field_hash_or_none(json, field):
    return not json.get(field) or is_field_hash(json, field)


def is_field_int(json, field):
    return isinstance(json.get(field), int)


def is_field_convertible(json, field, value_to_bytes):
    try:
        if not json.get(field):
            return False
        value_to_bytes(json[field])
        return True
    except ValueError:
        return False


class Hasher:
    class HashTag(IntEnum):
        BLOB = 0
        LIST_BRANCH_NODE = 1
        LIST_NODE = 2
        MAP_NODE = 3
        MAP_BRANCH_NODE = 4

    @staticmethod
    def hash_node(left, right):
        left_raw = bytes.fromhex(left)
        right_raw = bytes.fromhex(right)
        data = struct.pack('>Bss', Hasher.HashTag.LIST_BRANCH_NODE, left_raw, right_raw)

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_single_none(left):
        left_raw = bytes.fromhex(left)
        data = struct.pack('>Bs', Hasher.HashTag.LIST_BRANCH_NODE, left_raw)

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_leaf(val, value_to_bytes):
        value_raw = value_to_bytes(val)
        data = struct.pack('>Bs', Hasher.HashTag.BLOB)

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_list_node(length, merkle_root):
        merkle_root_raw = bytes.fromhex(merkle_root)
        data = struct.pack('>BQs', Hasher.HashTag.LIST_NODE, length, merkle_root_raw)

        return crypto_hash_sha256(data)


class ProofListKey:
    def __init__(self, height, index):
        self.height = height
        self.index = index

    def leaf(self, index):
        return ProofListKey(0, index)

    def left(self):
        return ProofListKey(self.height - 1, self.index << 1)

    def right(self):
        return ProofListKey(self.height - 1, (self.index << 1) + 1)


class ProofParser:
    NODE_CONDITIONS = {
        'Left': lambda self, json: is_field_dict(json, 'left') and is_field_hash_or_none(json, 'right'),
        'Right': lambda self, json: is_field_hash(json, 'left') and is_field_dict(json, 'right'),
        'Full': lambda self, json: is_field_dict(json, 'left') and is_field_dict(json, 'right'),
        'Leaf': lambda self, json: is_field_convertible(json, 'val', self.value_to_bytes),
        'Absent': lambda self, json: is_field_int(json, 'length') and is_field_hash(json, 'hash'),
    }

    NODE_FACTORY = {
        'Left': lambda self, json: ListProof.Left(self.parse(json['left']), json.get('right')),
        'Right': lambda self, json: ListProof.Right(json['left'], self.parse(json['right'])),
        'Full': lambda self, json: ListProof.Full(self.parse(json['left']), self.parse(json['right'])),
        'Leaf': lambda self, json: ListProof.Leaf(json['val']),
        'Absent': lambda self, json: ListProof.Absent(json['length'], json['hash']),
    }

    def __init__(self, value_to_bytes):
        self.value_to_bytes = value_to_bytes

    def parse(self, json):
        if is_dict(json):
            for kind, condition in ProofParser.NODE_CONDITIONS.items():
                if condition(self, json):
                    return ProofParser.NODE_FACTORY[kind](self, json)

        raise MalformedProofError('Received malformed proof: {}'.format(json))


class ListProof:
    Left = collections.namedtuple('Left', ['left', 'right'])
    Right = collections.namedtuple('Right', ['left', 'right'])
    Full = collections.namedtuple('Full', ['left', 'right'])
    Leaf = collections.namedtuple('Leaf', ['val'])
    Absent = collections.namedtuple('Absent', ['length', 'hash'])

    def __init__(self, proof_json, value_to_bytes=bytes.fromhex):
        self.value_to_bytes = value_to_bytes

        proof_parser = ProofParser(self.value_to_bytes)
        self._proof = proof_parser.parse(proof_json)

    def validate(self, length, expected_hash):
        pass

    def _collect(self, key, result):
        if key.height == 0:
            raise ListProofVerificationError('Unexpected branch')
