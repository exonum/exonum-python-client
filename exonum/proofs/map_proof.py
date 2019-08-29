from typing import Optional, Dict, Any, List
from functools import total_ordering
from enum import IntEnum

from ..errors import MalformedProofError
from .hasher import Hasher
from .utils import is_field_hash, to_bytes, div_ceil, trailing_zeros, reset_bits, leb128_encode_unsigned

# Size in bytes of the Hash. Equal to the hash function output (32).
KEY_SIZE = 32
# Size in bytes of the ProofPath.
PROOF_PATH_SIZE = KEY_SIZE + 2


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

        Paramaeters
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

    @staticmethod
    def from_bytes(data_bytes: bytes) -> 'ProofPath':
        """
        Builds a ProofPath from bytes sequence.

        Paramaeters
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
                if i < self.start() or i > self.end():
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

    def __lt__(self, other) -> bool:
        if self.start() != other.start():
            return NotImplemented

        if self.start() != 0:
            # the code below does not work if `self.start() % 8 != 0` without additional modifications.
            raise ValueError("Attempt to compare path with start != 0")

        right_bit = min(self.end(), other.end())
        right = div_ceil(right_bit, 8)

        raw_key = self.raw_key()
        other_raw_key = other.raw_key()

        for i in range(right):
            self_byte, other_byte = raw_key[i], other_raw_key[i]

            if i + 1 == right and right_bit % 8 != 0:
                # Cut possible junk after the end of path(s)
                tail = right_bit % 8
                self_byte = reset_bits(self_byte, tail)
                other_byte = reset_bits(other_byte, tail)

            # Try to find a first bit index at which this path is greater than the other path
            # (i.e., a bit of this path is 1 and the corresponding bit of the other path
            # is 0), and vice versa. The smaller of these indexes indicates the actual
            # larger path. In turn, the indexes can be found by counting trailing zeros.
            self_zeros = trailing_zeros(self_byte & ~other_byte)
            other_zeros = trailing_zeros(~self_byte & other_byte)

            if other_zeros != self_zeros:
                return other_zeros < self_zeros

        return self.end() < other.end()

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
        if end:
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

        from_byte = from_bit // 8
        to_byte = min(div_ceil(self.end(), 8), div_ceil(other.end(), 8))
        len_to_the_end = min(len(self), len(other))  # Maximum possible match length.

        raw_key = self.raw_key()
        other_raw_key = other.raw_key()

        for i in range(from_byte, to_byte):
            x = raw_key[i] ^ other_raw_key[i]
            if x != 0:
                tail = trailing_zeros(x)
                return min(i * 8 + tail - self.start(), len_to_the_end)

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


class MapProofEntry:
    def __init__(self, path: ProofPath, data_hash: bytes):
        self.path = path
        self.hash = data_hash

    def __repr__(self) -> str:
        return 'Entry [path: {}, hash: {}]'.format(self.path, self.hash)

    @staticmethod
    def parse(data: Dict[str, str]) -> 'MapProofEntry':
        """ Parses MapProofEntry from the json. """

        if not isinstance(data.get('path'), str) or not is_field_hash(data, 'hash'):
            raise MalformedProofError('Malformed proof element: {}'.format(data))

        path_bits = data['path']
        path = ProofPath.parse(path_bits)

        data_hash = to_bytes(data['hash'])

        return MapProofEntry(path, data_hash)


class OptionalEntry:
    def __init__(self, key: Any, value: Optional[Any]):
        self.key = key
        self.value = value
        self.is_missing = False if value else True

    def __repr__(self) -> str:
        if self.is_missing:
            return 'Missing [key: {}]'.format(self.key)
        else:
            return 'Entry [key: {}, value: {}]'.format(self.key, self.value)

    @staticmethod
    def parse(data: Dict[str, Any]) -> 'OptionalEntry':
        if data.get('missing'):
            return OptionalEntry(key=data['missing'], value=None)
        elif data.get('key') and data.get('value'):
            return OptionalEntry(key=data['key'], value=data['value'])
        else:
            raise MalformedProofError('Malformed entry: {}'.format(data))


def collect(entries: List[MapProofEntry]) -> bytes:
    """ TODO: write a proper docstring. """
    def common_prefix(x: ProofPath, y: ProofPath) -> ProofPath:
        return x.prefix(x.common_prefix_len(y))

    def hash_branch(left_child: MapProofEntry, right_child: MapProofEntry) -> bytes:
        # TODO

        return bytes()

    def fold(contour: List[MapProofEntry], last_prefix: ProofPath) -> Optional[ProofPath]:
        last_entry = contour.pop()
        penultimate_entry = contour.pop()

        contour.append(MapProofEntry(path=last_prefix, data_hash=hash_branch(penultimate_entry, last_entry)))

        if len(contour) > 1:
            penultimate_entry = contour[len(contour) - 2]
            return common_prefix(penultimate_entry.path, last_prefix)
        else:
            return None

    if len(entries) == 0:
        # TODO return default hash
        return bytes()
    elif len(entries) == 1:
        if entries[0].path.is_leaf():
            return Hasher.hash_single_entry_map(entries[0].path, entries[0].hash)
        else:
            # TODO raise error
            pass
    else:
        # Ah, here it goes...
        pass

    return bytes()


class MapProof:
    def __init__(self, entries: List[OptionalEntry], proof: List[MapProofEntry]):
        self.entries = entries
        self.proof = proof

    def __repr__(self) -> str:
        format_str = 'MapProof [\n  Entries: {}\n  Proof: {}\n]\n'

        return format_str.format(self.entries, self.proof)

    @staticmethod
    def parse(data: Dict[str, Any]) -> 'MapProof':
        if not data.get('entries') or not data.get('proof'):
            raise MalformedProofError('Malformed proof: {}'.format(data))

        entries: List[OptionalEntry] = [OptionalEntry.parse(raw_entry) for raw_entry in data['entries']]
        proof: List[MapProofEntry] = [MapProofEntry.parse(raw_entry) for raw_entry in data['proof']]

        return MapProof(entries, proof)
