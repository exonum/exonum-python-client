from typing import Dict, List, Tuple, Any, Callable
import itertools

from ..utils import is_field_hash, is_field_int, calculate_height
from ..hasher import Hasher
from .key import ProofListKey
from .errors import MalformedListProofError, ListProofVerificationError


class HashedEntry:
    """ Element of a proof with a key and hash. """
    def __init__(self, key: ProofListKey, entry_hash: bytes):
        self.key = key
        self.entry_hash = entry_hash

    @classmethod
    def parse(cls, data: Dict[Any, Any]) -> 'HashedEntry':
        """ Creates a HashedEntry object from provided dict. """
        if not isinstance(data, dict) or not is_field_hash(data, 'hash'):
            raise MalformedListProofError.parse_error(str(dict))

        key = ProofListKey.parse(data)
        return HashedEntry(key, bytes.fromhex(data['hash']))

    def __eq__(self, other) -> bool:
        return self.key == other.key and self.entry_hash == other.entry_hash


def _hash_layer(layer: List[HashedEntry], last_index: int) -> List[HashedEntry]:
    """ Takes a layer as a list of hashed entries and last index as int and returns new layer. """
    new_len = (len(layer) + 1) // 2
    new_layer: List[HashedEntry] = []

    for i in range(new_len):
        left_idx = 2 * i
        right_idx = 2 * i + 1

        # Check if there is both right and left indices in the layer.
        if len(layer) > right_idx:
            # Verify that entries in the correct order.
            if not layer[left_idx].key.is_left() or layer[right_idx].key.index != layer[left_idx].key.index + 1:
                raise MalformedListProofError.missing_hash()

            left_hash = layer[left_idx].entry_hash
            right_hash = layer[right_idx].entry_hash
            new_entry = HashedEntry(layer[left_idx].key.parent(), Hasher.hash_node(left_hash, right_hash))
        else:
            # If there is an odd number of entries, the index of last one should be equal to provided last_index.
            full_layer_length = last_index + 1
            if full_layer_length % 2 == 0 or layer[left_idx].key.index != last_index:
                raise MalformedListProofError.missing_hash()

            left_hash = layer[left_idx].entry_hash
            new_entry = HashedEntry(layer[left_idx].key.parent(), Hasher.hash_single_node(left_hash))
        new_layer.append(new_entry)

    return new_layer


class ListProof:
    def __init__(
        self,
        proof: List[HashedEntry],
        entries: List[Tuple[int, Any]],
        length: int,
        value_to_bytes: Callable[[Any], bytes]
    ):
        """
        Constructor of the ListProof.
        It's not intended to be used directly, use ListProof.Parse instead.

        Parameters
        ----------
        proof : List[HashedEntry]
            Proof entries.
        entries: List[Tuple[int, Any]]
            Unhashed entries (leaves).
        length: int
            Length of the proof list.
        value_to_bytes: Callable[[str], bytes]
            A function that converts the stored value to bytes for hashing.
        """
        self._proof = proof
        self._entries = entries
        self._length = length
        self._value_to_bytes = value_to_bytes

    @classmethod
    def parse(cls, proof_dict: Dict[str, Any], value_to_bytes: Callable[[Any], bytes] = bytes.fromhex) -> 'ListProof':
        """
        Method to parse a ListProof from a dict.
        Expected dict format:
        {
            'proof': [
                {'index': 1, 'height': 1, 'hash': 'eae60adeb5c681110eb5226a4ef95faa4f993c4a838d368b66f7c98501f2c8f9'}
            ],
            'entries': [
                [0, '6b70d869aeed2fe090e708485d9f4b4676ae6984206cf05efc136d663610e5c9']
            ],
            'length': 2
        }
        If no errors occured during parsing, a ListProof object will be returned.
        However, successfull parsing doesn't mean that proof isn't malformed (it only means that provided dict structure
        matches the expected one).
        Actual checks for the proof contents correctness will be performed in the `validate` method.

        To convert value to bytes ListProof attemts to use bytes.fromhex by default.
        If your type should be converted to bytes using protobuf, you can generate the converter function with use of
        `build_encoder_function` from encoder.py
        Otherwise, you have to implement converter function by yourself.

        Parameters
        ----------
        proof_dict : Dict[str, Any]
            Proof as a dict.
        value_to_bytes: Callable[[str], bytes]
            A function that converts the stored value to bytes for hashing.
            By default, `bytes.fromhex` is used.

        Raises
        ------
        MalformedListProofError
            If structure of the provided dict doesn't match expected one,
            an exception `MalformedListProofError` is raised.
        """
        if not isinstance(proof_dict.get('proof'), list) \
                or not isinstance(proof_dict.get('entries'), list) \
                or not is_field_int(proof_dict, 'length'):
            raise MalformedListProofError.parse_error(str(proof_dict))

        proof = [HashedEntry.parse(entry) for entry in proof_dict['proof']]
        entries = [cls._parse_entry(entry) for entry in proof_dict['entries']]
        length = proof_dict['length']

        return ListProof(proof, entries, length, value_to_bytes)

    def validate(self, expected_hash: bytes) -> List[Tuple[int, Any]]:
        """
        This method validates the provided proof against the given expected hash.

        Parameters
        ----------
        expected_hash: bytes
            Hexadecimal expected hash as bytes.

        Returns
        -------
        result: List[Tuple[int, Any]]
            If the hash is correct, a list of the collected values with indices is returned.

        Raises
        ------
        ListProofVerificationError
            If verification failed, an exception `ListProofVerificationError` is raised.
        MalformedListProofError
            If proof is malformed, an exception `MalformedListProofError` is raised.
        """
        if not isinstance(expected_hash, bytes):
            raise ValueError("expected_hash should be bytes")

        tree_root = self._collect()

        calculated_hash = Hasher.hash_list_node(self._length, tree_root)
        if calculated_hash == expected_hash:
            return self._entries
        else:
            raise ListProofVerificationError(expected_hash, calculated_hash)

    @staticmethod
    def _parse_entry(data: List[Any]):
        if not isinstance(data, list) or not len(data) == 2:
            raise MalformedListProofError.parse_error(str(data))
        return data[0], data[1]

    @staticmethod
    def _tree_height_by_length(length: int) -> int:
        if length == 0:
            return 0
        else:
            return calculate_height(length)

    def _collect(self) -> bytes:
        def _hash_entry(entry: Tuple[int, Any]) -> HashedEntry:
            """ Creates a hash entry from value. """
            key = ProofListKey(1, entry[0])
            entry_hash = Hasher.hash_leaf(self._value_to_bytes(entry[1]))
            return HashedEntry(key, entry_hash)

        def _split_hashes_by_height(hashes: List[HashedEntry], h: int) -> Tuple[List[HashedEntry], List[HashedEntry]]:
            """ Splits list of hashed entries into two lists by the given height. """
            current = list(itertools.takewhile(lambda x: x.key.height == h, hashes))
            remaining = hashes[len(current):]

            return current, remaining

        tree_height = self._tree_height_by_length(self._length)

        # Check an edge case when the list contains no elements.
        if tree_height == 0 and (not self._proof or not self._entries):
            raise MalformedListProofError.non_empty_proof()

        # If there are no entries, the proof should contain only a single root hash.
        if not self._entries:
            if len(self._proof) != 1:
                if self._proof:
                    raise MalformedListProofError.missing_hash()
                raise MalformedListProofError.unexpected_branch()

            if self._proof[0].key == ProofListKey(tree_height, 0):
                return self._proof[0].entry_hash

            raise MalformedListProofError.unexpected_branch()

        # Sort entries and proof.
        self._entries.sort(key=lambda el: el[0])
        self._proof.sort(key=lambda el: el.key)

        # Check that there is no duplicates.
        for idx in range(1, len(self._entries)):
            if self._entries[idx][0] == self._entries[idx - 1][0]:
                raise MalformedListProofError.duplicate_key()

        for idx in range(1, len(self._proof)):
            if self._proof[idx].key == self._proof[idx - 1].key:
                raise MalformedListProofError.duplicate_key()

        # Check that hashes on each height have indices in the allowed range.
        for entry in self._proof:
            height = entry.key.height
            if height == 0:
                raise MalformedListProofError.unexpected_leaf()

            # self._length -1 is the index of the last element at `height = 1`.
            # This index is divided by 2 with each new height.
            if height >= tree_height or entry.key.index > (self._length - 1) >> (height - 1):
                raise MalformedListProofError.unexpected_branch()

        # Create the first layer.
        layer = list(map(_hash_entry, self._entries))
        hashes = [hash_entry for hash_entry in self._proof]
        last_index = self._length - 1

        for height in range(1, tree_height):
            # Filter hashes of current height and the rest ones (to be processed later).
            hashes, remaining_hashes = _split_hashes_by_height(hashes, height)

            # Merge current layer with hashes that belong to this layer.
            layer = sorted(layer + hashes, key=lambda x: x.key)

            # Calculate new layer
            layer = _hash_layer(layer, last_index)

            # Size of the next layer is two times smaller.
            last_index //= 2

            # Make remaining_hashes hashes to be processed.
            hashes = remaining_hashes

        assert len(layer) == 1, "Result layer length is not 1"
        return layer[0].entry_hash
