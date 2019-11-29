""" Module with a MapProof Representation of the Branch Node. """
from logging import getLogger

from exonum_client.crypto import Hash
from .constants import PROOF_PATH_SIZE
from .proof_path import ProofPath
from ..hasher import Hasher

# pylint: disable=C0103
logger = getLogger(__name__)


class BranchNode:
    """ MapProof representation of the branch node. """

    # Branch node contains 2 proof paths and 2 hashes:
    BRANCH_NODE_SIZE = 2 * (Hasher.HASH_SIZE + PROOF_PATH_SIZE)

    def __init__(self) -> None:
        self.raw = bytearray([0] * self.BRANCH_NODE_SIZE)

    @staticmethod
    def _verify_kind(kind: str) -> None:
        if kind not in ["left", "right"]:
            logger.warning("Incorrect child kind: %s. Should be one of these: 'left', 'right'.", kind)
            raise ValueError("Incorrect child kind: {}".format(kind))

    def _hash_slice(self, kind: str) -> slice:
        self._verify_kind(kind)
        start = 0 if kind == "left" else Hasher.HASH_SIZE

        return slice(start, start + Hasher.HASH_SIZE)

    def _path_slice(self, kind: str) -> slice:
        self._verify_kind(kind)
        start = 2 * Hasher.HASH_SIZE if kind == "left" else 2 * Hasher.HASH_SIZE + PROOF_PATH_SIZE

        return slice(start, start + PROOF_PATH_SIZE)

    def child_hash(self, kind: str) -> Hash:
        """Returns a stored child hash for the specified kind ("left" or "right")."""
        return Hash(bytes(self.raw[self._hash_slice(kind)]))

    def child_path(self, kind: str) -> ProofPath:
        """Returns a stored child path for the specified kind ("left" or "right")."""
        return ProofPath(self.raw[self._path_slice(kind)], 0)

    def set_child_path(self, kind: str, prefix: ProofPath) -> None:
        """Sets a child path for the specified kind ("left" or "right")."""
        self.raw[self._path_slice(kind)] = prefix.as_bytes()

    def set_child_hash(self, kind: str, child_hash: Hash) -> None:
        """Sets a child hash for the specified kind ("left" or "right")."""
        self.raw[self._hash_slice(kind)] = child_hash.value

    def set_child(self, kind: str, prefix: ProofPath, child_hash: Hash) -> None:
        """Sets a child (both path and hash) for specified kind ("left" or "right")."""
        self.set_child_path(kind, prefix)
        self.set_child_hash(kind, child_hash)

    def object_hash(self) -> Hash:
        """Returns a hash of the branch node."""
        data = bytearray()

        data += self.raw[self._hash_slice("left")]
        data += self.raw[self._hash_slice("right")]

        left_path_compressed = self.child_path("left").as_bytes_compressed()
        data += left_path_compressed

        right_path_compressed = self.child_path("right").as_bytes_compressed()
        data += right_path_compressed

        return Hasher.hash_map_branch(data)
