from enum import IntEnum
import struct

from pysodium import crypto_hash_sha256


class Hasher:
    class HashTag(IntEnum):
        BLOB = 0
        LIST_BRANCH_NODE = 1
        LIST_NODE = 2
        MAP_NODE = 3
        MAP_BRANCH_NODE = 4

    @staticmethod
    def hash_node(left, right):
        data = struct.pack('<B', Hasher.HashTag.LIST_BRANCH_NODE) + left + right

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_single_node(left):
        data = struct.pack('<B', Hasher.HashTag.LIST_BRANCH_NODE) + left

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_leaf(val):
        data = struct.pack('<B', Hasher.HashTag.BLOB) + val

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_list_node(length, merkle_root):
        data = struct.pack('<BQ', Hasher.HashTag.LIST_NODE, length) + merkle_root

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_map_node(root):
        data = struct.pack('<B', Hasher.HashTag.MAP_NODE) + root

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_map_branch(branch_node):
        data = struct.pack('<B', Hasher.HashTag.MAP_BRANCH_NODE) + branch_node

        return crypto_hash_sha256(data)

    @staticmethod
    def hash_single_entry_map(path, hash):
        data = struct.pack('<B', Hasher.HashTag.MAP_BRANCH_NODE) + path.as_bytes() + hash

        return crypto_hash_sha256(data)
