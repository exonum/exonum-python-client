"""ProofPath Module."""
from typing import Optional
from functools import total_ordering
from enum import IntEnum
from logging import getLogger

from ..utils import div_ceil, reset_bits, leb128_encode_unsigned

from .constants import KEY_SIZE, PROOF_PATH_SIZE
from .errors import MalformedMapProofError

# pylint: disable=C0103
logger = getLogger(__name__)


@total_ordering
class ProofPath:
    """ProofPath is a representation of the key in MapProof."""

    class _KeyPrefix(IntEnum):
        BRANCH = 0
        LEAF = 1
        VALUE = 2

    class _Positions(IntEnum):
        KIND_POS = 0
        KEY_POS = 1
        LEN_POS = KEY_SIZE + 1

    @staticmethod
    def parse(bits: str) -> "ProofPath":
        """
        This method parses a ProofPath from a string.

        Parameters
        -----------
        bits: str
            Sequence of '0' and '1' as a string.

        Returns
        -------
        ProofPath
            Parsed ProofPath object.

        Raises
        ------
        MalformedProofError
            If an input string is incorrect (too long, empty or contains unexpected symbols).
        """

        length = len(bits)
        if length == 0 or length > 8 * KEY_SIZE:
            error = "Incorrect MapProof path length: {}".format(length)
            logger.warning(error)
            raise MalformedMapProofError.malformed_entry(bits, error)

        data = [0] * KEY_SIZE

        for i, char in enumerate(bits):
            if char == "0":
                pass
            elif char == "1":
                data[i // 8] += 1 << (i % 8)
            else:
                error = "Unexpected MapProof path symbol: {}".format(char)
                logger.warning(error)
                raise MalformedMapProofError.malformed_entry(bits, error)

        data_bytes = bytes(data)

        proof_path = ProofPath.from_bytes(data_bytes)
        if length != 8 * KEY_SIZE:
            proof_path = proof_path.prefix(length)

        logger.debug("Successfully parsed a ProofPath from a string.")
        return proof_path

    @staticmethod
    def from_bytes(data_bytes: bytes) -> "ProofPath":
        """
        Builds ProofPath from a byte sequence.

        Parameters
        -----------
        data_bytes: bytes
            Array of bytes with ProofPath data.

        Returns
        -------
        ProofPath
            Parsed ProofPath object.

        Raises
        ------
        ValueError
            Length of provided array is not equal to KEY_SIZE constant.
        """
        if len(data_bytes) != KEY_SIZE:
            logger.warning("Wrong length of the provided byte sequence: expected %s, got %s", KEY_SIZE, len(data_bytes))
            raise ValueError("Incorrect data size")

        inner = bytearray([0] * PROOF_PATH_SIZE)

        inner[0] = ProofPath._KeyPrefix.LEAF
        inner[ProofPath._Positions.KEY_POS : ProofPath._Positions.KEY_POS + KEY_SIZE] = data_bytes[:]
        inner[ProofPath._Positions.LEN_POS] = 0

        return ProofPath(inner, 0)

    def __init__(self, data_bytes: bytearray, start: int):
        """ Constructor of ProofPath. Expects arguments to be cleaned already and does not check anything. """
        self.data_bytes = data_bytes
        self._start = start

    def __repr__(self) -> str:
        """ Conversion to a string. """
        bits_str = ""

        raw_key = self.raw_key()
        for byte_idx, chunk in enumerate(raw_key):
            # Range from 7 to 0 inclusively:
            for bit in range(7, -1, -1):
                i = byte_idx * 8 + bit
                if i < self.start() or i >= self.end():
                    bits_str += "_"
                else:
                    bits_str += "0" if (1 << bit) & chunk == 0 else "1"

            bits_str += "|"

        format_str = "ProofPath [ start: {}, end: {}, bits: {} ]".format(self.start(), self.end(), bits_str)
        return format_str

    def __len__(self) -> int:
        return self.end() - self.start()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProofPath):
            raise TypeError("Attempt to compare ProofPath with an object of a different type.")
        return len(self) == len(other) and self.starts_with(other)

    def bit(self, idx: int) -> int:
        """Returns a bit of the path at the specified position."""
        pos = self.start() + idx
        chunk = self.raw_key()[(pos // 8)]
        bit = pos % 8
        return ((1 << bit) & chunk) >> bit

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ProofPath):
            raise TypeError("Attempt to compare ProofPath with an object of a different type.")

        if self.start() != other.start():
            return NotImplemented

        if self.start() != 0:
            # The code below does not work if `self.start() % 8 != 0` without additional modifications:
            raise ValueError("Comparison is allowed only for paths with start =0")

        this_len = len(self)
        other_len = len(other)

        intersecting_bits = min(this_len, other_len)

        pos = self.common_prefix_len(other)

        if pos == intersecting_bits:
            return this_len < other_len

        return self.bit(pos) < other.bit(pos)

    def is_leaf(self) -> bool:
        """ Returns True if ProofPath is a leaf. Otherwise returns False """
        return self.data_bytes[0] == ProofPath._KeyPrefix.LEAF

    def start(self) -> int:
        """ Returns the index of the start bit. """
        return self._start

    def end(self) -> int:
        """ Returns the index of the end bit. """
        if self.is_leaf():
            return KEY_SIZE * 8

        return self.data_bytes[ProofPath._Positions.LEN_POS]

    def raw_key(self) -> bytes:
        """ Returns the stored key as raw bytes. """
        return bytes(self.data_bytes[ProofPath._Positions.KEY_POS : ProofPath._Positions.KEY_POS + KEY_SIZE])

    def set_end(self, end: Optional[int]) -> None:
        """ Sets the right border of the proof path. """
        if end is not None:
            self.data_bytes[0] = self._KeyPrefix.BRANCH
            self.data_bytes[self._Positions.LEN_POS] = end
        else:
            self.data_bytes[0] = self._KeyPrefix.LEAF
            self.data_bytes[self._Positions.LEN_POS] = 0

    def prefix(self, length: int) -> "ProofPath":
        """ Creates a copy of this path shortened to the specified length. """

        end = self._start + length
        key_len = KEY_SIZE * 8

        if end >= key_len:
            err_msg = f"Length of the prefix ({end}) should not be greater than KEY_SIZE * 8 ({key_len})."
            logger.warning(err_msg)
            raise ValueError(err_msg)

        key = ProofPath(bytearray(self.data_bytes), self._start)
        key.set_end(end)

        return key

    def match_len(self, other: "ProofPath", from_bit: int) -> int:
        """ Returns the length of the common segment. """
        if self.start() != other.start():
            logger.warning("Misaligned bit ranges: %s != %s", self.start(), other.start())
            raise ValueError("Misaligned bit ranges")

        if from_bit < self.start() or from_bit > self.end():
            err_msg = f"Incorrect from_bit value: {from_bit}"
            logger.warning(err_msg)
            raise ValueError(err_msg)

        len_to_the_end = min(len(self), len(other))
        for i in range(from_bit, len_to_the_end):
            if self.bit(i) != other.bit(i):
                return i

        return len_to_the_end

    def common_prefix_len(self, other: "ProofPath") -> int:
        """ Returns the length of the common prefix. """
        if self.start() == other.start():
            return self.match_len(other, self.start())

        return 0

    def starts_with(self, other: "ProofPath") -> bool:
        """ Returns True if `other` is a prefix of `self`. Otherwise returns False. """
        return self.common_prefix_len(other) == len(other)

    def as_bytes(self) -> bytes:
        """ Represents a path as bytes according to the Merkledb implementation. """

        return bytes(self.data_bytes)

    def as_bytes_compressed(self) -> bytes:
        """ Represents a path as compressed bytes using les128 algorigthm. """
        bits_len = self.end()
        whole_bytes_len = div_ceil(bits_len, 8)

        key = self.raw_key()[0:whole_bytes_len]

        result = bytearray()
        result += leb128_encode_unsigned(bits_len)
        result += key

        # Trim insignificant bits in the last byte:
        bits_in_last_byte = bits_len % 8
        if whole_bytes_len > 0 and bits_in_last_byte != 0:
            tail = self.end() % 8
            result[-1] = reset_bits(result[-1], tail)

        return bytes(result)
