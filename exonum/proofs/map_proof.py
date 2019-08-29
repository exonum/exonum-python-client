from typing import Optional, Dict
from enum import IntEnum

from ..errors import MalformedProofError
from .utils import is_field_hash, to_bytes

# Size in bytes of the Hash. Equal to the hash function output (32).
KEY_SIZE = 32
# Size in bytes of the ProofPath.
PROOF_PATH_SIZE = KEY_SIZE + 2


class ProofPath:
    class KeyPrefix(IntEnum):
        BRANCH = 0
        LEAF = 1
        VALUE = 2

    class Positions(IntEnum):
        KIND_POS = 0
        KEY_POS = 1
        LEN_POS = KEY_SIZE + 1

    @staticmethod
    def parse(bits: str) -> ProofPath:
        """ Parses a ProofPath from string. """

        length = len(bits)
        if length == 0 or length > 8 * KEY_SIZE:
            raise MalformedProofError('Incorrect MapProof path length: {}'.format(length))

        data = [0] * KEY_SIZE

        for i, ch in enumerate(bits):
            if ch == '0':
                pass
            elif ch == '1':
                data[i // 8] += 1 << (i % 8)
            else:
                raise MalformedProofError('Unexpected MapProof path symbol: {}'.format(ch))

        data_bytes = bytes(data)

        if length == 8 * KEY_SIZE:
            return ProofPath.from_bytes(data_bytes)
        else:
            return ProofPath.from_bytes(data_bytes).prefix(length)

    def __init__(self, data_bytes: bytearray, start: int):
        self.data_bytes = data_bytes
        self.start = start

    @staticmethod
    def from_bytes(data_bytes: bytes) -> ProofPath:
        """ Builds a proof from bytes sequence. """
        inner = bytearray([0] * PROOF_PATH_SIZE)

        inner[0] = ProofPath.KeyPrefix.LEAF
        inner[ProofPath.Positions.KEY_POS:ProofPath.Positions.LEN_POS] = data_bytes[:]
        inner[ProofPath.Positions.LEN_POS] = 0

        return ProofPath(inner, 0)

    def set_end(self, end: Optional[int]):
        """ Sets tha right border of the proof path. """
        if end:
            self.data_bytes[0] = self.KeyPrefix.BRANCH
            self.data_bytes[self.Positions.LEN_POS] = end
        else:
            self.data_bytes[0] = self.KeyPrefix.LEAF
            self.data_bytes[self.Positions.LEN_POS] = 0

    def prefix(self, length) -> ProofPath:
        """ Creates a copy of this path shortened to the specified length. """

        end = self.start + length
        key_len = KEY_SIZE * 8

        if end >= key_len:
            raise ValueError('Length of prefix ({}) should not be greater than KEY_SIZE * 8'.format(end))

        key = ProofPath(bytearray(self.data_bytes), self.start)
        key.set_end(end)

        return key

    def as_bytes(self) -> bytes:
        """ Represents path as bytes according to the Merkledb implementation. """

        return bytes(self.data_bytes)

    def as_bytes_compressed(self) -> bytes:
        """ Represents path as compressed bytes using les128 algorigthm. """
        pass


class MapProofEntry:
    def __init__(self, path: ProofPath, data_hash: bytes):
        self.path = path
        self.hash = data_hash

    @staticmethod
    def parse(data: Dict[str, str]):
        """ Parses MapProofEntry from the json. """

        if not isinstance(data.get('path'), str) or not is_field_hash(data, 'hash'):
            raise MalformedProofError('Malformed proof entry: {}'.format(data))

        path_bits = data['path']
        path = ProofPath.parse(path_bits)

        data_hash = to_bytes(data['hash'])

        return MapProofEntry(path, data_hash)


class MapProof:
    pass
