"""Proof Verification Module for Exonum `ProofListIndex`."""

from typing import Dict, List, Tuple, Any, Callable
import itertools
from logging import getLogger

from exonum_client.crypto import Hash
from ..utils import is_field_hash, is_field_int, calculate_height
from ..hasher import Hasher
from .key import ProofListKey
from .errors import MalformedListProofError, ListProofVerificationError

# pylint: disable=C0103
logger = getLogger(__name__)


class HashedEntry:
    """ Element of a proof with a key and a hash. """

    def __init__(self, key: ProofListKey, entry_hash: Hash):
        self.key = key
        self.entry_hash = entry_hash

    @classmethod
    def parse(cls, data: Dict[Any, Any]) -> "HashedEntry":
        """ Creates a HashedEntry object from the provided dict. """
        if not isinstance(data, dict) or not is_field_hash(data, "hash"):
            err = MalformedListProofError.parse_error(str(data))
            logger.warning(
                "Could not parse `hash` from dict, which is required for HashedEntry object creation. %s", str(err)
            )
            raise err

        key = ProofListKey.parse(data)
        return HashedEntry(key, Hash(bytes.fromhex(data["hash"])))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HashedEntry):
            raise TypeError("Attempt to compare HashedEntry with an object of a different type.")
        return self.key == other.key and self.entry_hash == other.entry_hash


def _hash_layer(layer: List[HashedEntry], last_index: int) -> List[HashedEntry]:
    """ Takes a layer as a list of hashed entries and the last index as an int and returns a new layer. """
    new_len = (len(layer) + 1) // 2
    new_layer: List[HashedEntry] = []

    for i in range(new_len):
        left_idx = 2 * i
        right_idx = 2 * i + 1

        # Check if there are both right and left indices in the layer:
        if len(layer) > right_idx:
            # Verify that entries are in the correct order:
            if not layer[left_idx].key.is_left() or layer[right_idx].key.index != layer[left_idx].key.index + 1:
                err = MalformedListProofError.missing_hash()
                logger.warning(str(err))
                raise err

            left_hash = layer[left_idx].entry_hash
            right_hash = layer[right_idx].entry_hash
            new_entry = HashedEntry(layer[left_idx].key.parent(), Hasher.hash_node(left_hash, right_hash))
        else:
            # If there is an odd number of entries, the index of the last one should be equal to provided last_index:
            full_layer_length = last_index + 1
            if full_layer_length % 2 == 0 or layer[left_idx].key.index != last_index:
                err = MalformedListProofError.missing_hash()
                logger.warning(str(err))
                raise err

            left_hash = layer[left_idx].entry_hash
            new_entry = HashedEntry(layer[left_idx].key.parent(), Hasher.hash_single_node(left_hash))
        new_layer.append(new_entry)

    return new_layer


class ListProof:
    """ListProof class provides an interface to parse and verify proofs for ProofListIndex retrieved
    from the Exonum blockchain.

    Example workflow:

    >>> proof_json = {
    >>>     "proof": [
    >>>         {"index": 1, "height": 1, "hash": "eae60adeb5c681110eb5226a4ef95faa4f993c4a838d368b66f7c98501f2c8f9"}
    >>>     ],
    >>>     "entries": [[0, "6b70d869aeed2fe090e708485d9f4b4676ae6984206cf05efc136d663610e5c9"]],
    >>>     "length": 2,
    >>> }
    >>> expected_hash = "07df67b1a853551eb05470a03c9245483e5a3731b4b558e634908ff356b69857"
    >>> proof = ListProof.parse(proof_json)
    >>> result = proof.validate(bytes.fromhex(expected_hash))
    >>> assert result == [(0, stored_val)]
    """

    def __init__(
        self,
        proof: List[HashedEntry],
        entries: List[Tuple[int, Any]],
        length: int,
        value_to_bytes: Callable[[Any], bytes],
    ):
        """
        Constructor of the ListProof.
        It is not intended to be used directly, use ListProof.Parse instead.

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
    def parse(cls, proof_dict: Dict[str, Any], value_to_bytes: Callable[[Any], bytes] = bytes.fromhex) -> "ListProof":
        """
        Method to parse ListProof from the dict.

        Expected dict format:

        >>>
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
        However, successfull parsing does not mean that the proof is not malformed (it only means that the provided
        dict structure matches the expected one).
        Actual checks for the proof contents correctness will be performed in the `validate` method.

        To convert value to bytes, ListProof attemts to use bytes.fromhex by default.
        If your type should be converted to bytes using Protobuf, you can generate a converter function with the use of
        `build_encoder_function` from encoder.py.
        Otherwise, you have to implement the converter function by yourself.

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
            If the structure of the provided dict does not match the expected one,
            an exception `MalformedListProofError` is raised.
        """
        if (
            not isinstance(proof_dict.get("proof"), list)
            or not isinstance(proof_dict.get("entries"), list)
            or not is_field_int(proof_dict, "length")
        ):
            err = MalformedListProofError.parse_error(str(proof_dict))
            logger.warning("The structure of the provided dict does not match the expected one. %s", str(err))
            raise err

        proof = [HashedEntry.parse(entry) for entry in proof_dict["proof"]]
        entries = [cls._parse_entry(entry) for entry in proof_dict["entries"]]
        length = proof_dict["length"]

        logger.debug("Successfully parsed ListProof from the dict.")
        return ListProof(proof, entries, length, value_to_bytes)

    def validate(self, expected_hash: Hash) -> List[Tuple[int, Any]]:
        """
        This method validates the provided proof against the given expected hash.

        Parameters
        ----------
        expected_hash: Hash
            Expected root hash.

        Returns
        -------
        result: List[Tuple[int, Any]]
            If the hash is correct, a list of the collected values with indices is returned.

        Raises
        ------
        ListProofVerificationError
            If verification fails, an exception `ListProofVerificationError` is raised.
        MalformedListProofError
            If the proof is malformed, an exception `MalformedListProofError` is raised.
        """
        if not isinstance(expected_hash, Hash):
            raise TypeError("`expected_hash` should be of type Hash.")

        tree_root = self._collect()

        calculated_hash = Hasher.hash_list_node(self._length, tree_root)
        if calculated_hash != expected_hash:
            logger.warning("Provided root hash does not match the calculated one.")
            raise ListProofVerificationError(expected_hash.value, calculated_hash.value)
        logger.debug("Successfully validated the provided proof against the given expected hash.")

        return self._entries

    @staticmethod
    def _parse_entry(data: List[Any]) -> Tuple[int, Any]:
        if not isinstance(data, list) or not len(data) == 2:
            err = MalformedListProofError.parse_error(str(data))
            logger.warning("Could not parse a list. %s", err)
            raise err
        return data[0], data[1]

    @staticmethod
    def _tree_height_by_length(length: int) -> int:
        if length == 0:
            return 0

        return calculate_height(length)

    @staticmethod
    def _check_duplicates(entries: List[Any]) -> None:
        for idx in range(1, len(entries)):
            if entries[idx][0] == entries[idx - 1][0]:
                err = MalformedListProofError.duplicate_key()
                logger.warning(str(err))
                raise err

    def _collect(self) -> Hash:
        def _hash_entry(entry: Tuple[int, Any]) -> HashedEntry:
            """ Creates a hash entry from the value. """
            key = ProofListKey(1, entry[0])
            entry_hash = Hasher.hash_leaf(self._value_to_bytes(entry[1]))
            return HashedEntry(key, entry_hash)

        def _split_hashes_by_height(
            hashes: List[HashedEntry], height: int
        ) -> Tuple[List[HashedEntry], List[HashedEntry]]:
            """ Splits a list of the hashed entries into two lists by the given height. """
            current = list(itertools.takewhile(lambda x: x.key.height == height, hashes))
            remaining = hashes[len(current) :]

            return current, remaining

        tree_height = self._tree_height_by_length(self._length)

        # Check an edge case when the list contains no elements:
        if tree_height == 0 and (not self._proof or not self._entries):
            err = MalformedListProofError.non_empty_proof()
            logger.warning(str(err))
            raise err

        # If there are no entries, the proof should contain only a single root hash:
        if not self._entries:
            if len(self._proof) != 1:
                if self._proof:
                    err = MalformedListProofError.missing_hash()
                    logger.warning(str(err))
                    raise err
                err = MalformedListProofError.unexpected_branch()
                logger.warning(str(err))
                raise err

            if self._proof[0].key == ProofListKey(tree_height, 0):
                return self._proof[0].entry_hash

            err = MalformedListProofError.unexpected_branch()
            logger.warning(str(err))
            raise err

        # Sort the entries and the proof:
        self._entries.sort(key=lambda el: el[0])
        self._proof.sort(key=lambda el: el.key)

        # Check that there are no duplicates:
        self._check_duplicates(self._entries)
        self._check_duplicates(self._proof)

        # Check that the hashes at each height have indices in the allowed range:
        for entry in self._proof:
            height = entry.key.height
            if height == 0:
                err = MalformedListProofError.unexpected_leaf()
                logger.warning(str(err))
                raise err

            # self._length -1 is the index of the last element at `height = 1`.
            # This index is divided by 2 with each new height:
            if height >= tree_height or entry.key.index > (self._length - 1) >> (height - 1):
                err = MalformedListProofError.unexpected_branch()
                logger.warning(str(err))
                raise err

        # Create the first layer:
        layer = list(map(_hash_entry, self._entries))
        hashes = list(self._proof)
        last_index = self._length - 1

        for height in range(1, tree_height):
            # Filter the hashes of the current height and the rest heights (to be processed later):
            hashes, remaining_hashes = _split_hashes_by_height(hashes, height)

            # Merge the current layer with the hashes that belong to this layer:
            layer = sorted(layer + hashes, key=lambda x: x.key)

            # Calculate a new layer:
            layer = _hash_layer(layer, last_index)

            # Size of the next layer is two times smaller:
            last_index //= 2

            # Make remaining_hashes hashes to be processed:
            hashes = remaining_hashes

        assert len(layer) == 1, "Result layer length is not 1"
        return layer[0].entry_hash
