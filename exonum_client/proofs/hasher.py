"""Module with Hashing Utils for Proofs."""
from enum import IntEnum
import struct

# From pysodium import crypto_hash_sha256, crypto_hash_sha256_BYTES
from exonum_client.crypto import HASH_BYTES_LEN, Hash

# Default hash value for empty ProofMapIndex.
EMPTY_MAP_HASH = bytes.fromhex("7324b5c72b51bb5d4c180f1109cfd347b60473882145841c39f3e584576296f9")


class Hasher:
    """Hasher class performs hashing operations on proof elements."""

    HASH_SIZE = HASH_BYTES_LEN
    DEFAULT_HASH = bytes([0] * HASH_BYTES_LEN)

    class HashTag(IntEnum):
        """Prefixes for different types of nodes."""

        BLOB = 0
        LIST_BRANCH_NODE = 1
        LIST_NODE = 2
        MAP_NODE = 3
        MAP_BRANCH_NODE = 4

    @staticmethod
    def hash_raw_data(data: bytes) -> Hash:
        """ SHA256 hash of the provided data. """

        return Hash.hash_data(data)

    @staticmethod
    def hash_node(left: Hash, right: Hash) -> Hash:
        """ Convenience method to obtain a hashed value of the merkle tree node. """

        data = struct.pack("<B", Hasher.HashTag.LIST_BRANCH_NODE) + left.value + right.value

        return Hash.hash_data(data)

    @staticmethod
    def hash_single_node(left: Hash) -> Hash:
        """ Convenience method to obtain a hashed value of the merkle tree node with one child. """

        data = struct.pack("<B", Hasher.HashTag.LIST_BRANCH_NODE) + left.value

        return Hash.hash_data(data)

    @staticmethod
    def hash_leaf(val: bytes) -> Hash:
        """ Convenience method to obtain a hashed value of the merkle tree leaf. """

        data = struct.pack("<B", Hasher.HashTag.BLOB) + val

        return Hash.hash_data(data)

    @staticmethod
    def hash_list_node(length: int, merkle_root: Hash) -> Hash:
        """
        Hash of the list object.
        ```text
        h = sha-256( HashTag::ListNode || len as u64 || merkle_root )
        ```
        """
        data = struct.pack("<BQ", Hasher.HashTag.LIST_NODE, length) + merkle_root.value

        return Hash.hash_data(data)

    @staticmethod
    def hash_map_node(root: Hash) -> Hash:
        """
        Hash of the map object.
        ```text
        h = sha-256( HashTag::MapNode || merkle_root )
        ```
        """
        data = struct.pack("<B", Hasher.HashTag.MAP_NODE) + root.value

        return Hash.hash_data(data)

    @staticmethod
    def hash_map_branch(branch_node: bytes) -> Hash:
        """
        Hash of the map branch node.
        ```text
        h = sha-256( HashTag::MapBranchNode || <left_key> || <right_key> || <left_hash> || <right_hash> )
        ```
        """
        data = struct.pack("<B", Hasher.HashTag.MAP_BRANCH_NODE) + branch_node

        return Hash.hash_data(data)

    @staticmethod
    def hash_single_entry_map(path: bytes, child_hash: Hash) -> Hash:
        """
        Hash of the map with single entry.
        ``` text
        h = sha-256( HashTag::MapBranchNode || <key> || <child_hash> )
        ```
        """
        data = struct.pack("<B", Hasher.HashTag.MAP_BRANCH_NODE) + path + child_hash.value

        return Hash.hash_data(data)
