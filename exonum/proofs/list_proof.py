from typing import List, Tuple, Any

import collections

from ..errors import MalformedProofError, ListProofVerificationError
from .utils import *
from .hasher import Hasher


class ProofListKey:
    def __init__(self, height, index):
        self._height = height
        self._index = index

    def leaf(self, index):
        return ProofListKey(0, index)

    def left(self):
        return ProofListKey(self._height - 1, self._index << 1)

    def right(self):
        return ProofListKey(self._height - 1, (self._index << 1) + 1)

    def index(self):
        return self._index

    def height(self):
        return self._height


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

    def validate(self, length: int, merkle_root: str):
        result: List[Tuple[int, Any]] = []

        height = calculate_height(length)

        try:
            root_hash = self._collect(self._proof, ProofListKey(height, 0), result)
        except ListProofVerificationError as error:
            return False, error

        expected_hash = bytes.fromhex(merkle_root)

        if type(self._proof) == ListProof.Absent:
            if root_hash != bytes.fromhex(merkle_root):
                return False, ListProofVerificationError('Unmatched root hash')
        else:
            result_hash = Hasher.hash_list_node(length, root_hash)
            if result_hash != expected_hash:
                return False, ListProofVerificationError('Unmatched root hash')

        return True, result

    def _collect(self, proof_el, key, result):
        if key.height == 0:
            raise ListProofVerificationError('Unexpected branch')

        data_hash = None

        if type(proof_el) == ListProof.Full:
            left_hash = self._collect(proof_el.left, key.left(), result)
            right_hash = self._collect(proof_el.right, key.right(), result)

            data_hash = Hasher.hash_node(left_hash, right_hash)

        elif type(proof_el) == ListProof.Left:
            left_hash = self._collect(proof_el.left, key.left(), result)

            if proof_el.right:
                data_hash = Hasher.hash_node(left_hash, proof_el.right)
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
