from enum import IntEnum
import struct

from pysodium import crypto_hash_sha256, crypto_hash_sha256_BYTES

# Default hash value for empty ProofMapIndex.
EMPTY_MAP_HASH = bytes.fromhex('7324b5c72b51bb5d4c180f1109cfd347b60473882145841c39f3e584576296f9')


class Hasher:
    HASH_SIZE = crypto_hash_sha256_BYTES

    class HashTag(IntEnum):
        BLOB = 0
        LIST_BRANCH_NODE = 1
        LIST_NODE = 2
        MAP_NODE = 3
        MAP_BRANCH_NODE = 4

    @staticmethod
    def hash_raw_data(data: bytes) -> bytes:
        return crypto_hash_sha256(data)

    @staticmethod
    def hash_node(left: bytes, right: bytes) -> bytes:
        data = struct.pack('<B', Hasher.HashTag.LIST_BRANCH_NODE) + left + right

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_single_node(left: bytes) -> bytes:
        data = struct.pack('<B', Hasher.HashTag.LIST_BRANCH_NODE) + left

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_leaf(val: bytes) -> bytes:
        data = struct.pack('<B', Hasher.HashTag.BLOB) + val

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_list_node(length: int, merkle_root: bytes) -> bytes:
        data = struct.pack('<BQ', Hasher.HashTag.LIST_NODE, length) + merkle_root

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_map_node(root: bytes) -> bytes:
        data = struct.pack('<B', Hasher.HashTag.MAP_NODE) + root

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_map_branch(branch_node: bytes) -> bytes:
        data = struct.pack('<B', Hasher.HashTag.MAP_BRANCH_NODE) + branch_node

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_single_entry_map(path, h: bytes) -> bytes:
        data = struct.pack('<B', Hasher.HashTag.MAP_BRANCH_NODE) + path.as_bytes() + h

        return crypto_hash_sha256(data)
