from typing import Optional, Dict, Any, List, Iterator, Callable
from functools import total_ordering
from enum import IntEnum

from .proof_path import ProofPath
from .errors import MalformedMapProofError
from .constants import KEY_SIZE, PROOF_PATH_SIZE
from .optional_entry import OptionalEntry
from .branch_node import BranchNode
from ..hasher import Hasher, EMPTY_MAP_HASH
from ..utils import is_field_hash, to_bytes, div_ceil, trailing_zeros, reset_bits, leb128_encode_unsigned


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
            raise MalformedMapProofError.malformed_entry(data)

        path_bits = data['path']
        path = ProofPath.parse(path_bits)

        data_hash = to_bytes(data['hash'])

        return MapProofEntry(path, data_hash)


def collect(entries: List[MapProofEntry]) -> bytes:
    def common_prefix(x: ProofPath, y: ProofPath) -> ProofPath:
        return x.prefix(x.common_prefix_len(y))

    def hash_branch(left_child: MapProofEntry, right_child: MapProofEntry) -> bytes:
        branch = BranchNode()
        branch.set_child('left', left_child.path, left_child.hash)
        branch.set_child('right', right_child.path, right_child.hash)

        return branch.object_hash()

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
        return EMPTY_MAP_HASH  # TODO is it correct?
    elif len(entries) == 1:
        if entries[0].path.is_leaf():
            return Hasher.hash_single_entry_map(entries[0].path, entries[0].hash)
        else:
            raise MalformedMapProofError.non_terminal_node(entries[0].path)
    else:
        # Contour of entries to be folded into result hash.
        contour: List[MapProofEntry] = []

        # Initical contour state.
        first_entry, second_entry = entries[0], entries[1]
        last_prefix = common_prefix(first_entry.path, second_entry.path)
        contour = [first_entry, second_entry]

        # Process the rest of the entries.
        for entry in entries[2:]:
            new_prefix = common_prefix(contour[-1].path, entry.path)

            # Fold contour from the last added entry to the beginning.
            # At each iteration two last entries are taken and attempted to fold into one new entry.
            while len(contour) > 1 and len(new_prefix) < len(last_prefix):
                prefix = fold(contour, last_prefix)
                if prefix:
                    last_prefix = prefix

            contour.append(entry)
            last_prefix = new_prefix

        # All entries are processed. Fold the contour into the final hash.
        while len(contour) > 1:
            prefix = fold(contour, last_prefix)
            if prefix:
                last_prefix = prefix

        return contour[0].hash


class CheckedMapProof:
    def __init__(self, entries: List[OptionalEntry], root_hash: bytes):
        self._entries = entries
        self._root_hash = root_hash

    def missing_keys(self) -> Iterator[OptionalEntry]:
        """ Retrieves entries that the proof shows as missing from the map. """
        return filter(lambda el: el.is_missing, self._entries)

    def entries(self) -> Iterator[OptionalEntry]:
        """ Retrieves entries that the proof shows as present in the map. """
        return filter(lambda el: not el.is_missing, self._entries)

    def all_entries(self) -> List[OptionalEntry]:
        """ Retrieves all entries in the proof. """
        return self._entries

    def root_hash(self) -> bytes:
        """ Returns a hash of the map that this proof is constructed for. """
        return self._root_hash


class MapProof:
    def __init__(
        self,
        entries: List[OptionalEntry],
        proof: List[MapProofEntry],
        key_to_bytes: Callable[[Any], bytes],
        value_to_bytes: Callable[[Any], bytes]
    ):
        self.entries = entries
        self.proof = proof
        self._key_to_bytes = key_to_bytes
        self._value_to_bytes = value_to_bytes

    def __repr__(self) -> str:
        format_str = 'MapProof [\n  Entries: {}\n  Proof: {}\n]\n'

        return format_str.format(self.entries, self.proof)

    @staticmethod
    def parse(
        data: Dict[str, Any],
        key_to_bytes: Callable[[Any], bytes],
        value_to_bytes: Callable[[Any], bytes]
    ) -> 'MapProof':
        if data.get('entries') is None or data.get('proof') is None:
            raise MalformedMapProofError.malformed_entry(data)

        entries: List[OptionalEntry] = [OptionalEntry.parse(raw_entry) for raw_entry in data['entries']]
        proof: List[MapProofEntry] = [MapProofEntry.parse(raw_entry) for raw_entry in data['proof']]

        return MapProof(entries, proof, key_to_bytes, value_to_bytes)

    def _check_proof(self, proof):
        for idx in range(1, len(proof)):
            prev_path, path = proof[idx - 1].path, proof[idx].path

            if prev_path < path:
                if path.starts_with(prev_path):
                    raise MalformedMapProofError.embedded_paths(prev_path, path)
            elif prev_path == path:
                raise MalformedMapProofError.duplicate_path(path)
            elif prev_path > path:
                raise MalformedMapProofError.invalid_ordering(prev_path, path)
            else:
                assert False, "Incomparable keys in proof"

    def check(self) -> CheckedMapProof:
        def kv_to_map_entry(kv: OptionalEntry) -> MapProofEntry:
            key_bytes = self._key_to_bytes(kv.key)
            key_hash = Hasher.hash_raw_data(key_bytes)

            path = ProofPath.from_bytes(key_hash)
            value_hash = Hasher.hash_leaf(self._value_to_bytes(kv.value))

            return MapProofEntry(path, value_hash)

        proof = self.proof[:]

        entries = filter(lambda el: not el.is_missing, self.entries)

        proof += map(lambda el: kv_to_map_entry(el), self.entries)

        proof.sort(key=lambda el: el.path)

        self._check_proof(proof)

        result = collect(proof)

        return CheckedMapProof(self.entries, result)
