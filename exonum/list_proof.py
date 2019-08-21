from typing import List, Tuple, Any

import collections
import struct
from enum import IntEnum
from pysodium import crypto_hash_sha256

from .errors import MalformedProofError, ListProofVerificationError


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


def to_bytes(hex_data):
    return bytes.fromhex(hex_data)


def calculate_height(number):
    if number < 0:
        raise ValueError("Number {} is less than zero".format(number))
    elif number == 0:
        return 1
    else:
        # Amount of trailing zeroes for the next power of two
        # This works because we can calculate the next power of two as 1 << (number - 1).bit_length()
        # So, (number - 1).bit_length() is the shift => there will be that amount of trailing zeroes in number.
        trailing_zeroes_amount = (number - 1).bit_length()

        return trailing_zeroes_amount + 1


class Hasher:
    class HashTag(IntEnum):
        BLOB = 0
        LIST_BRANCH_NODE = 1
        LIST_NODE = 2
        MAP_NODE = 3
        MAP_BRANCH_NODE = 4

    @staticmethod
    def hash_node(left, right):
        data = struct.pack('>Bss', Hasher.HashTag.LIST_BRANCH_NODE, left_raw, right_raw)

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_single_none(left):
        data = struct.pack('>Bs', Hasher.HashTag.LIST_BRANCH_NODE, left_raw)

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_leaf(val):
        data = struct.pack('>Bs', Hasher.HashTag.BLOB)

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_list_node(length, merkle_root):
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

    def index(self):
        return self.index

    def height(self):
        return self.height


class ProofParser:
    NODE_CONDITIONS = {
        'Left': lambda self, json: is_field_dict(json, 'left') and is_field_hash_or_none(json, 'right'),
        'Right': lambda self, json: is_field_hash(json, 'left') and is_field_dict(json, 'right'),
        'Full': lambda self, json: is_field_dict(json, 'left') and is_field_dict(json, 'right'),
        'Leaf': lambda self, json: is_field_convertible(json, 'val', self.value_to_bytes),
        'Absent': lambda self, json: is_field_int(json, 'length') and is_field_hash(json, 'hash'),
    }

    NODE_FACTORY = {
        'Left': lambda self, json: ListProof.Left(self.parse(json['left']), to_bytes(json.get('right'))),
        'Right': lambda self, json: ListProof.Right(to_bytes(json['left']), self.parse(json['right'])),
        'Full': lambda self, json: ListProof.Full(self.parse(json['left']), self.parse(json['right'])),
        'Leaf': lambda self, json: ListProof.Leaf(json['val'], self.value_to_bytes(json['val'])),
        'Absent': lambda self, json: ListProof.Absent(json['length'], to_bytes(json['hash'])),
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
    Leaf = collections.namedtuple('Leaf', ['val', 'val_raw'])
    Absent = collections.namedtuple('Absent', ['length', 'hash'])

    def __init__(self, proof_json, value_to_bytes=bytes.fromhex):
        self.value_to_bytes = value_to_bytes

        proof_parser = ProofParser(self.value_to_bytes)
        self._proof = proof_parser.parse(proof_json)

    def validate(self, length: int, expected_hash: str):
        result: List[Tuple[int, Any]] = []

        height = calculate_height(length)

        try:
            root_hash = self._collect(self._proof, ProofListKey(height, 0), result)
        except ListProofVerificationError as error:
            return False, error

        if type(self._proof) == ListProof.Absent:
            if root_hash != bytes.fromhex(expected_hash):
                return False, ListProofVerificationError('Unmatched root hash')
        else:
            if Hasher.hash_list_node(length, root_hash) != bytes.fromhex(expected_hash):
                return False, ListProofVerificationError('Unmatched root hash')

        return True, result

    def _collect(self, proof_el, key, result):
        if key.height == 0:
            raise ListProofVerificationError('Unexpected branch')

        data_hash = None

        if type(proof_el) == ListProof.Full:
            left_hash = self._collect(proof_el.left, key.left(), result)
            right_hash = self._collect(proof_el.right, key.left(), result)

            data_hash = Hasher.hash_node(left_hash, right_hash)

        elif type(proof_el) == ListProof.Left:
            left_hash = self._collect(proof_el.left, key.left(), result)

            if proof_el.right:
                data_hash = Hasher.hash_node(left_hash, proof_elright)
            else:
                data_hash = Hasher.hash_single_none(left_hash)

        elif type(proof_el) == ListProof.Right:
            right_hash = self._collect(proof_el.right, key.right(), result)

            data_hash = self.hash_node(proof_el.left, right_hash)

        elif type(proof_el) == ListProof.Leaf:
            if key.height() > 1:
                raise ListProofVerificationError('Unexpected leaf')

            result.append((key.index(), proof_el.val))

            data_hash = Hasher.hash_leaf(proof_el.val_raw)

        elif type(proof_el) == ListProof.Absent:
            data_hash = Hasher.hash_list_node(proof_el.length, proof_el.hash)

        else:
            assert False, "Got wrong element in ListProof._collect: {}".format(proof_el)

        return data_hash
