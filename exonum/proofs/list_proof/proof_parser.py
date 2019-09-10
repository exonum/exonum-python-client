from typing import List, Tuple, Any

import collections

from .list_proof_element import ListProofElement, ListProofElementType
from .errors import MalformedListProofError, ListProofVerificationError
from ..hasher import Hasher
from ..utils import (
    is_field_dict,
    is_field_hash,
    is_field_hash_or_none,
    is_field_convertible,
    is_field_int,
    to_bytes,
    is_dict
)


class ProofParser:
    NODE_CONDITIONS = {
        # Node is Left when it contains field 'left' which is dict and may contain field 'right' which is hash.
        'Left': lambda _, data: is_field_dict(data, 'left') and is_field_hash_or_none(data, 'right'),

        # Node is Right when it contains field 'left' which is hash and field 'right' which is dict.
        'Right': lambda _, data: is_field_hash(data, 'left') and is_field_dict(data, 'right'),

        # Node is Full, when it contains fields 'left' and 'right' and both of them are dicts.
        'Full': lambda _, data: is_field_dict(data, 'left') and is_field_dict(data, 'right'),

        # Node is Leaf when it contains field 'val' which can be converted to bytes with provided function.
        'Leaf': lambda self, data: is_field_convertible(data, 'val', self._value_to_bytes),

        # Node is Absent when it contains field 'length' which is int and field 'hash' which is hexadecimal string.
        'Absent': lambda _, data: is_field_int(data, 'length') and is_field_hash(data, 'hash'),
    }

    NODE_FACTORY = {
        # Left node contains left subtree and right value hash as bytes.
        'Left': lambda self, data: ListProofElement.Left(self.parse(data['left']), to_bytes(data.get('right'))),

        # Right node contains left value hash as bytes and right subtree.
        'Right': lambda self, data: ListProofElement.Right(to_bytes(data['left']), self.parse(data['right'])),

        # Full node contains left and right subtrees.
        'Full': lambda self, data: ListProofElement.Full(self.parse(data['left']), self.parse(data['right'])),

        # Leaf node contains value converted to bytes with the provided function.
        'Leaf': lambda self, data: ListProofElement.Leaf(data['val'], self._value_to_bytes(data['val'])),

        # Absent node contains length as int and hash as bytes.
        'Absent': lambda self, data: ListProofElement.Absent(data['length'], to_bytes(data['hash'])),
    }

    def __init__(self, value_to_bytes):
        self._value_to_bytes = value_to_bytes

    def parse(self, proof_dict) -> ListProofElementType:
        if is_dict(proof_dict):
            for kind, condition in ProofParser.NODE_CONDITIONS.items():
                if condition(self, proof_dict):
                    return ProofParser.NODE_FACTORY[kind](self, proof_dict)

        raise MalformedListProofError('Received malformed proof: {}'.format(proof_dict))
