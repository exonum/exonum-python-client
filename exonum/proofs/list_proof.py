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
        # Node is Left when it conains field 'left' which is dict and may contain field 'right' which is hash.
        'Left': lambda self, data: is_field_dict(data, 'left') and is_field_hash_or_none(data, 'right'),

        # Node is Right when it contains field 'left' which is hash and field 'right' which is dict.
        'Right': lambda self, data: is_field_hash(data, 'left') and is_field_dict(data, 'right'),

        # Node is Full, when it contains fields 'left' and 'right' and both of them are dicts.
        'Full': lambda self, data: is_field_dict(data, 'left') and is_field_dict(data, 'right'),

        # Node is Leaf when it contains field 'val' which can be converted to bytes with provided function.
        'Leaf': lambda self, data: is_field_convertible(data, 'val', self.value_to_bytes),

        # Node is Absent when it contains field 'length' which is int and field 'hash' which is hexademical string.
        'Absent': lambda self, data: is_field_int(data, 'length') and is_field_hash(data, 'hash'),
    }

    NODE_FACTORY = {
        # Left node contains left subtree and right value hash as bytes.
        'Left': lambda self, json: ListProof.Left(self.parse(json['left']), to_bytes(json.get('right'))),

        # Right node contains left value hash as bytes and right subtree.
        'Right': lambda self, json: ListProof.Right(to_bytes(json['left']), self.parse(json['right'])),

        # Full node contains left and right subtrees.
        'Full': lambda self, json: ListProof.Full(self.parse(json['left']), self.parse(json['right'])),

        # Leaf node contains value converted to bytes with the provided function.
        'Leaf': lambda self, json: ListProof.Leaf(json['val'], self.value_to_bytes(json['val'])),

        # Absent node contains length as int and hash as bytes.
        'Absent': lambda self, json: ListProof.Absent(json['length'], to_bytes(json['hash'])),
    }

    def __init__(self, value_to_bytes):
        self.value_to_bytes = value_to_bytes

    def parse(self, proof_dict):
        if is_dict(proof_dict):
            for kind, condition in ProofParser.NODE_CONDITIONS.items():
                if condition(self, proof_dict):
                    return ProofParser.NODE_FACTORY[kind](self, proof_dict)

        raise MalformedProofError('Received malformed proof: {}'.format(proof_dict))


class ListProof:
    Left = collections.namedtuple('Left', ['left', 'right'])
    Right = collections.namedtuple('Right', ['left', 'right'])
    Full = collections.namedtuple('Full', ['left', 'right'])
    Leaf = collections.namedtuple('Leaf', ['val', 'val_raw'])
    Absent = collections.namedtuple('Absent', ['length', 'hash'])

    def __init__(self, proof_dict, value_to_bytes=bytes.fromhex):
        """
        Constructor of the ListProof.

        Parameters
        ----------
        proof_dict : Dict[Any, Any]
            Proof as a python dictionary.
        value_to_bytes: Callable[[str], bytes]
            A function that converts the stored value to bytes for hashing.
            By default, `bytes.fromhex` is used.
        """

        self.value_to_bytes = value_to_bytes

        proof_parser = ProofParser(self.value_to_bytes)
        self._proof = proof_parser.parse(proof_dict)

    def validate(self, length: int, expected_hash: str):
        """
        This method validates the provided proof against the given expected hash.

        Parameters
        ----------
        length : int
            Length of the proof list.
        expected_hash: str
            Hexadecimal string with the expected hash.

        Returns
        -------
        hash_valid: bool
            Boolean value denoting if the expected hash equals to the hash obtained from the proof.
        result: List[Tuple[int, Any]] or ListProofVerificationError
            If the hash is correct, a list of the collected values with indices is returned.
            Otherwise, ListProofVerificationError with the string denoting the type of the verification error.
        """

        result: List[Tuple[int, Any]] = []

        height = calculate_height(length)

        try:
            root_hash = self._collect(self._proof, ProofListKey(height, 0), result)
        except ListProofVerificationError as error:
            return False, error

        expected_hash_raw = bytes.fromhex(expected_hash)

        if type(self._proof) == ListProof.Absent:
            if root_hash != expected_hash_raw:
                return False, ListProofVerificationError('Unmatched root hash')
        else:
            result_hash = Hasher.hash_list_node(length, root_hash)
            if result_hash != expected_hash_raw:
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
