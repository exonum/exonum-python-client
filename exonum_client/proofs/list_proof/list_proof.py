"""Proof Verification Module for Exonum `ProofListIndex`."""

from typing import List, Tuple, Any, Dict, Callable

from exonum_client.crypto import Hash
from .key import ProofListKey
from .list_proof_element import ListProofElement, ListProofElementType
from .proof_parser import ProofParser
from .errors import MalformedListProofError, ListProofVerificationError
from ..utils import calculate_height
from ..hasher import Hasher


class ListProof:
    """ListProof class provides an interface to parse and verify proofs for ProofListIndex retrieved
    from the Exonum blockchain.

    Example workflow:

    >>> proof_json = {
    >>>     'left': {
    >>>         'val': '2dc17ca9c00d29ecff475d92f9b0c8885350d7b783e703b8ad21ae331d134496'
    >>>     },
    >>>     'right': 'c6f5873ab0f93c8be05e4e412cfc307fd98e58c9da9e6f582130882e672eb742'
    >>> }
    >>> expected_hash = "07df67b1a853551eb05470a03c9245483e5a3731b4b558e634908ff356b69857"
    >>> proof = ListProof.parse(proof_json)
    >>> result = proof.validate(2, bytes.fromhex(expected_hash))
    >>> assert result == [(0, stored_val)]
    """

    def __init__(self, proof: ListProofElementType, value_to_bytes: Callable[[Any], bytes]) -> None:
        """
        Constructor of the ListProof.
        It is not intended to be used directly, use ListProof.Parse instead.
        """

        self.value_to_bytes = value_to_bytes
        self._proof = proof

    @classmethod
    def parse(cls, proof_dict: Dict[str, Any], value_to_bytes: Callable[[Any], bytes] = bytes.fromhex) -> "ListProof":
        """
        Method to parse ListProof from the dict.

        Expected dict format:

        >>>
        {
            'left': {
                'val': '2dc17ca9c00d29ecff475d92f9b0c8885350d7b783e703b8ad21ae331d134496'
            },
            'right': 'c6f5873ab0f93c8be05e4e412cfc307fd98e58c9da9e6f582130882e672eb742'
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

        proof_parser = ProofParser(value_to_bytes)
        proof = proof_parser.parse(proof_dict)

        return cls(proof, value_to_bytes)

    def validate(self, length: int, expected_hash: Hash) -> List[Tuple[int, Any]]:
        """
        This method validates the provided proof against the given expected hash.

        Parameters
        ----------
        length : int
            Length of the proof list.
        expected_hash: Hash
            Hexadecimal string with the expected hash.

        Returns
        -------
        result: List[Tuple[int, Any]]
            If the hash is correct, a list of the collected values with indices is returned.

        Raises
        ------
        ListProofVerificationError
            If verification failed, an exception `ListProofVerificationError` is raised with the string denoting
            the type of the verification error.
        """

        root_hash, result = self._calculate_root_hash(length)

        if isinstance(self._proof, ListProofElement.Absent):
            if root_hash != expected_hash:
                raise ListProofVerificationError(root_hash.value, expected_hash.value)
        else:
            result_hash = Hasher.hash_list_node(length, root_hash)
            if result_hash != expected_hash:
                raise ListProofVerificationError(result_hash.value, expected_hash.value)

        return result

    def _calculate_root_hash(self, length: int) -> Tuple[Hash, List[Tuple[int, bytes]]]:
        # Absent proof element may be only the top one.
        if isinstance(self._proof, ListProofElement.Absent):
            root_hash = Hasher.hash_list_node(self._proof.length, Hash(self._proof.hash))

            return root_hash, []

        # Otherwise, we should calculate the root hash recursively.
        result: List[Tuple[int, Any]] = []

        height = calculate_height(length)

        root_hash = self._collect(self._proof, ProofListKey(height, 0), result)

        return root_hash, result

    def _collect(self, proof_el: ListProofElementType, key: ProofListKey, result: List[Tuple[int, bytes]]) -> Hash:
        if key.height == 0:
            raise MalformedListProofError.unexpected_branch()

        if isinstance(proof_el, ListProofElement.Full):
            left_hash = self._collect(proof_el.left, key.left(), result)
            right_hash = self._collect(proof_el.right, key.right(), result)

            data_hash = Hasher.hash_node(left_hash, right_hash)

        elif isinstance(proof_el, ListProofElement.Left):
            left_hash = self._collect(proof_el.left, key.left(), result)

            if proof_el.right:
                data_hash = Hasher.hash_node(left_hash, Hash(proof_el.right))
            else:
                data_hash = Hasher.hash_single_node(left_hash)

        elif isinstance(proof_el, ListProofElement.Right):
            right_hash = self._collect(proof_el.right, key.right(), result)

            data_hash = Hasher.hash_node(Hash(proof_el.left), right_hash)

        elif isinstance(proof_el, ListProofElement.Leaf):
            if key.height > 1:
                raise MalformedListProofError.unexpected_leaf()

            result.append((key.index, proof_el.val))

            data_hash = Hasher.hash_leaf(proof_el.val_raw)

        else:
            assert False, "Got wrong element in ListProof._collect: {}".format(proof_el)

        return data_hash
