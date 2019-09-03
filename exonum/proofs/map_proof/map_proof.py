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
        """ Parses MapProofEntry from the provided dict. """

        if not isinstance(data.get('path'), str) or not is_field_hash(data, 'hash'):
            raise MalformedMapProofError.malformed_entry(data)

        path_bits = data['path']
        path = ProofPath.parse(path_bits)

        data_hash = to_bytes(data['hash'])

        return MapProofEntry(path, data_hash)


def collect(entries: List[MapProofEntry]) -> bytes:
    """
    Computes the root hash of the Merkle Patricia tree backing the specified entries
    in the map view.
    The tree is not restored in full; instead, we add the paths to
    the tree in their lexicographic order (i.e., according to the `PartialOrd` implementatio
    of `ProofPath`) and keep track of the rightmost nodes (the right contour) of the tree.
    It is easy to see that adding paths in the lexicographic order means that only
    the nodes in the right contour may be updated on each step. Further, on each step
    zero or more nodes are evicted from the contour, and a single new node is
    added to it.
    `entries` are assumed to be sorted by the path in increasing order.
    """

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
    """ Version of `MapProof` obtained after verification. """
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
    """
    Proof of existence for a Map.

    This class is capable of parsing a MapProof from the Dict[Any, Any] and
    verifying parsed proof.

    In most cases you should not create MapProof manually (use MapProofBuilder instead).

    However, if you understand that MapProofBuilder doesn't suit your needs, here is the designed
    workflow example:

    ```python
    proof = get_proof_somehow()

    # Assuming that protobuf files for service already loaded and compiled.
    cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
    cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')

    cryptocurrency_decoder = MapProofBuilder.build_encoder_function(cryptocurrency_module.Wallet)

    # Keys will be encoded to bytes using "bytes.fromhex",
    # and values will be encoded using "Wallet" protobuf structure.
    parsed_proof = MapProof.parse(proof, lambda x: bytes.fromhex(x), cryptocurrency_decoder)

    # CheckedMapProof will be returned.
    result = parsed_proof.check()
    ```
    """

    def __init__(
        self,
        entries: List[OptionalEntry],
        proof: List[MapProofEntry],
        key_to_bytes: Callable[[Any], bytes],
        value_to_bytes: Callable[[Any], bytes]
    ):
        """
        Constructor of the MapProof. It shouldn't be called directly, use `MapProof.parse`.
        """
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
        """
        Method to parse the proof.

        Example of the expected proof format:

        ```python
        proof = {
          "entries": [
            {
              "key": "e610db75b0bbbd4c606c4f8ca3fca9f916e9c8ae9a93b5b767082172454344b3",
              "value": {
                "pub_key": {
                  "data": list(bytes.fromhex("e610db75b0bbbd4c606c4f8ca3fca9f916e9c8ae9a93b5b767082172454344b3"))
                },
                "name": "Alice1",
                "balance": 95,
                "history_len": 6,
                "history_hash": {
                  "data": list(bytes.fromhex("19faf859d7456907c76f085af5b7a2d7621d992617a349006c07720957d5d49d"))
                }
              }
            }
          ],
          "proof": [
            {
              "path": "010000100100100010100100110001100111011011011000010011011011111111110110001101001001011010111100"
                      "001010010011011010001110011001011001010101100100000101010010000001101011100000010011101101001011"
                      "1110010011011011101001110000111111000000011111100010001011010000",
              "hash": "dbeab4aa952e2c2cb3dc921aa42c9b508e2e5961cad2463f7203d228abc204c8"
            }
          ]
        }
        ```

        Parameters
        ----------
        data: Dict[str, Any]
            Name of the protobuf structure to be used in converted function.
        key_to_bytes: Callable[[Any], bytes]
            Function that will be used to convert keys to bytes.
        value_to_bytes: Callable[[Any], bytes]
            Function that will be used to convert values to bytes.

        Returns
        -------
        MapProof
            If parsing succeed, MapProof object will be returned.

        Raises
        ------
        MalformedMapProofError
            If the provided raw MapProof was malformed and parsing failed, this exception will
            be rised.
        """

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
        """
        Calculates the root hash from the parsed proof.

        Returns
        -------
        CheckedMapProof
            If no errors were occured during the calculation, a CheckedMapProof entity will be returned.

        Raises
        ------
        MalformedMapProofError
            If the provided raw MapProof was malformed and parsing failed, this exception will
            be rised.
        """

        def kv_to_map_entry(kv: OptionalEntry) -> MapProofEntry:
            key_bytes = self._key_to_bytes(kv.key)
            key_hash = Hasher.hash_raw_data(key_bytes)

            path = ProofPath.from_bytes(key_hash)
            value_hash = Hasher.hash_leaf(self._value_to_bytes(kv.value))

            return MapProofEntry(path, value_hash)

        proof = self.proof[:]

        actual_entries = filter(lambda el: not el.is_missing, self.entries)

        proof += map(lambda el: kv_to_map_entry(el), actual_entries)

        proof.sort(key=lambda el: el.path)

        self._check_proof(proof)

        result = collect(proof)

        return CheckedMapProof(self.entries, Hasher.hash_map_node(result))
