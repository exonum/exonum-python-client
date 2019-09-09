from typing import Optional, Dict, Any, List, Iterator, Callable
from functools import total_ordering
from enum import IntEnum

from ..hasher import Hasher, EMPTY_MAP_HASH
from ..utils import div_ceil, reset_bits, leb128_encode_unsigned

from .constants import KEY_SIZE, PROOF_PATH_SIZE
from .errors import MalformedMapProofError


@total_ordering
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
    def parse(bits: str) -> 'ProofPath':
        """
        This method parses a ProofPath from string.

        Parameters
        -----------
        bits: str
            Sequence of '0' and '1' as string.

        Returns
        -------
        ProofPath
            Parsed ProofPath object

        Raises
        ------
        MalformedProofError
            If the input string was incorrect (too long, empty or contain unexpected symbols).
        """

        length = len(bits)
        if length == 0 or length > 8 * KEY_SIZE:
            error = 'Incorrect MapProof path length: {}'.format(length)
            raise MalformedMapProofError.malformed_entry(bits, error)

        data = [0] * KEY_SIZE

        for i, ch in enumerate(bits):
            if ch == '0':
                pass
            elif ch == '1':
                data[i // 8] += 1 << (i % 8)
            else:
                error = 'Unexpected MapProof path symbol: {}'.format(ch)
                raise MalformedMapProofError.malformed_entry(bits, error)

        data_bytes = bytes(data)

        if length == 8 * KEY_SIZE:
            return ProofPath.from_bytes(data_bytes)
        else:
            return ProofPath.from_bytes(data_bytes).prefix(length)

    @staticmethod
    def from_bytes(data_bytes: bytes) -> 'ProofPath':
        """
        Builds a ProofPath from bytes sequence.

        Parameters
        -----------
        data_bytes: bytes
            Array of bytes with ProofPath data.

        Returns
        -------
        ProofPath
            Parsed ProofPath object

        Raises
        ------
        ValueError
            If the length of provided array is not equal to KEY_SIZE constant.
        """
        if len(data_bytes) != KEY_SIZE:
            raise ValueError('Incorrect data size')

        inner = bytearray([0] * PROOF_PATH_SIZE)

        inner[0] = ProofPath.KeyPrefix.LEAF
        inner[ProofPath.Positions.KEY_POS:ProofPath.Positions.KEY_POS + KEY_SIZE] = data_bytes[:]
        inner[ProofPath.Positions.LEN_POS] = 0

        return ProofPath(inner, 0)

    def __init__(self, data_bytes: bytearray, start: int):
        """ Constructor of the ProofPath. Expects arguments to be cleaned already and doesn't check anything. """
        self.data_bytes = data_bytes
        self._start = start

    def __repr__(self) -> str:
        """ Conversion to string. """
        bits_str = ''

        raw_key = self.raw_key()
        for byte_idx in range(len(raw_key)):
            chunk = raw_key[byte_idx]
            # Range from 7 to 0 inclusively.
            for bit in range(7, -1, -1):
                i = byte_idx * 8 + bit
                if i < self.start() or i >= self.end():
                    bits_str += '_'
                else:
                    bits_str += '0' if (1 << bit) & chunk == 0 else '1'

            bits_str += '|'

        format_str = 'ProofPath [ start: {}, end: {}, bits: {} ]'.format(self.start(), self.end(), bits_str)
        return format_str

    def __len__(self) -> int:
        return self.end() - self.start()

    def __eq__(self, other) -> bool:
        return len(self) == len(other) and self.starts_with(other)

    def bit(self, idx):
        pos = self.start() + idx
        chunk = self.raw_key()[(pos // 8)]
        bit = pos % 8
        return (1 << bit) & chunk

    def __lt__(self, other) -> bool:
        if self.start() != other.start():
            return NotImplemented

        if self.start() != 0:
            # the code below does not work if `self.start() % 8 != 0` without additional modifications.
            raise ValueError("Attempt to compare path with start != 0")

        this_len = len(self)
        other_len = len(other)

        intersecting_bits = min(this_len, other_len)

        pos = self.common_prefix_len(other)

        if pos == intersecting_bits:
            return this_len < other_len

        return self.bit(pos) < other.bit(pos)

    def is_leaf(self):
        """ Returns True if ProofPath is leaf and False otherwise """
        return self.data_bytes[0] == ProofPath.KeyPrefix.LEAF

    def start(self):
        """ Returns the index of the start bit. """
        return self._start

    def end(self):
        """ Returns the index of the end bit. """
        if self.is_leaf():
            return KEY_SIZE * 8
        else:
            return self.data_bytes[ProofPath.Positions.LEN_POS]

    def raw_key(self) -> bytes:
        """ Returns the stored key as raw bytes """
        return bytes(self.data_bytes[ProofPath.Positions.KEY_POS:ProofPath.Positions.KEY_POS + KEY_SIZE])

    def set_end(self, end: Optional[int]):
        """ Sets tha right border of the proof path. """
        if end is not None:
            self.data_bytes[0] = self.KeyPrefix.BRANCH
            self.data_bytes[self.Positions.LEN_POS] = end
        else:
            self.data_bytes[0] = self.KeyPrefix.LEAF
            self.data_bytes[self.Positions.LEN_POS] = 0

    def prefix(self, length) -> 'ProofPath':
        """ Creates a copy of this path shortened to the specified length. """

        end = self._start + length
        key_len = KEY_SIZE * 8

        if end >= key_len:
            raise ValueError('Length of prefix ({}) should not be greater than KEY_SIZE * 8'.format(end))

        key = ProofPath(bytearray(self.data_bytes), self._start)
        key.set_end(end)

        return key

    def match_len(self, other, from_bit) -> int:
        """ Returns the length of the common segment. """
        if self.start() != other.start():
            raise ValueError("Misaligned bit ranges")
        elif from_bit < self.start() or from_bit > self.end():
            raise ValueError("Incorrect from_bit value: {}".format(from_bit))

        len_to_the_end = min(len(self), len(other))
        for i in range(len_to_the_end):
            if self.bit(i) != other.bit(i):
                return i
        return len_to_the_end

    def common_prefix_len(self, other) -> int:
        """ Returns the length of the common prefix. """
        if self.start() == other.start():
            return self.match_len(other, self.start())
        else:
            return 0

    def starts_with(self, other) -> bool:
        """ Returns True if other is a prefix of self and False otherwise. """
        return self.common_prefix_len(other) == len(other)

    def as_bytes(self) -> bytes:
        """ Represents path as bytes according to the Merkledb implementation. """

        return bytes(self.data_bytes)

    def as_bytes_compressed(self) -> bytes:
        """ Represents path as compressed bytes using les128 algorigthm. """
        bits_len = self.end()
        whole_bytes_len = div_ceil(bits_len, 8)

        key = self.raw_key()[0:whole_bytes_len]

        result = bytearray()
        result += leb128_encode_unsigned(bits_len)
        result += key

        # Trim insignificant bits in the last byte.
        bits_in_last_byte = bits_len % 8
        if whole_bytes_len > 0 and bits_in_last_byte != 0:
            tail = self.end() % 8
            result[-1] = reset_bits(result[-1], tail)

        return bytes(result)
