from .constants import PROOF_PATH_SIZE
from .proof_path import ProofPath
from ..hasher import Hasher


class BranchNode:
    # Branch node contains 2 proof paths and 2 hashes.
    BRANCH_NODE_SIZE = 2 * (Hasher.HASH_SIZE + PROOF_PATH_SIZE)

    def __init__(self):
        self.raw = bytearray([0] * self.BRANCH_NODE_SIZE)

    def _verify_kind(self, kind):
        if kind not in ["left", "right"]:
            raise ValueError("Incorrect child kind: {}".format(kind))

    def _hash_slice(self, kind) -> slice:
        self._verify_kind(kind)
        start = 0 if kind == "left" else Hasher.HASH_SIZE

        return slice(start, start + Hasher.HASH_SIZE)

    def _path_slice(self, kind) -> slice:
        self._verify_kind(kind)
        start = 2 * Hasher.HASH_SIZE if kind == "left" else 2 * Hasher.HASH_SIZE + PROOF_PATH_SIZE

        return slice(start, start + PROOF_PATH_SIZE)

    def child_hash(self, kind: str) -> bytes:
        return bytes(self.raw[self._hash_slice(kind)])

    def child_path(self, kind: str) -> ProofPath:
        return ProofPath(self.raw[self._path_slice(kind)], 0)

    def set_child_path(self, kind: str, prefix: ProofPath):
        self.raw[self._path_slice(kind)] = prefix.as_bytes()

    def set_child_hash(self, kind: str, child_hash: bytes):
        if len(child_hash) != Hasher.HASH_SIZE:
            raise ValueError("Incorrect hash length: {}".format(child_hash))

        self.raw[self._hash_slice(kind)] = child_hash

    def set_child(self, kind: str, prefix: ProofPath, child_hash: bytes):
        self.set_child_path(kind, prefix)
        self.set_child_hash(kind, child_hash)

    def object_hash(self) -> bytes:
        data = bytearray()

        data += self.raw[self._hash_slice("left")]
        data += self.raw[self._hash_slice("right")]

        left_path_compressed = self.child_path("left").as_bytes_compressed()
        data += left_path_compressed

        right_path_compressed = self.child_path("right").as_bytes_compressed()
        data += right_path_compressed

        return Hasher.hash_map_branch(data)
