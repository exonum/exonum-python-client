from typing import List, Tuple, Any

from .key import ProofListKey
from .list_proof_element import ListProofElement
from .proof_parser import ProofParser
from .errors import MalformedListProofError, ListProofVerificationError
from ..utils import *
from ..hasher import Hasher


class ListProof:
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
        result: List[Tuple[int, Any]]
            If the hash is correct, a list of the collected values with indices is returned.

        Raises
        ------
        ListProofVerificationError
            If verification failed, an exception `ListProofVerificationError` is raised with the string denoting
            the type of the verification error.
        """

        root_hash, result = self._calculate_root_hash(length)

        expected_hash_raw = bytes.fromhex(expected_hash)

        if type(self._proof) == ListProofElement.Absent:
            if root_hash != expected_hash_raw:
                raise ListProofVerificationError('Unmatched root hash')
        else:
            result_hash = Hasher.hash_list_node(length, root_hash)
            if result_hash != expected_hash_raw:
                raise ListProofVerificationError('Unmatched root hash')

        return result

    def _calculate_root_hash(self, length):
        # Absent proof element may be only the top one.
        if type(self._proof) == ListProofElement.Absent:
            root_hash = Hasher.hash_list_node(self._proof.length, self._proof.hash)

            return root_hash, []

        # Otherwise, we should calculate the root hash recursively.
        result: List[Tuple[int, Any]] = []

        height = calculate_height(length)

        root_hash = self._collect(self._proof, ProofListKey(height, 0), result)

        return root_hash, result

    def _collect(self, proof_el, key, result):
        if key.height == 0:
            raise ListProofVerificationError('Unexpected branch')

        if type(proof_el) == ListProofElement.Full:
            left_hash = self._collect(proof_el.left, key.left(), result)
            right_hash = self._collect(proof_el.right, key.right(), result)

            data_hash = Hasher.hash_node(left_hash, right_hash)

        elif type(proof_el) == ListProofElement.Left:
            left_hash = self._collect(proof_el.left, key.left(), result)

            if proof_el.right:
                data_hash = Hasher.hash_node(left_hash, proof_el.right)
            else:
                data_hash = Hasher.hash_single_node(left_hash)

        elif type(proof_el) == ListProofElement.Right:
            right_hash = self._collect(proof_el.right, key.right(), result)

            data_hash = Hasher.hash_node(proof_el.left, right_hash)

        elif type(proof_el) == ListProofElement.Leaf:
            if key.height > 1:
                raise ListProofVerificationError('Unexpected leaf')

            result.append((key.index, proof_el.val))

            data_hash = Hasher.hash_leaf(proof_el.val_raw)

        else:
            assert False, "Got wrong element in ListProof._collect: {}".format(proof_el)

        return data_hash
