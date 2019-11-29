"""MapProof Module."""
from typing import Optional, Dict, Any, List, Iterator, Callable
from logging import getLogger

from exonum_client.crypto import Hash
from .proof_path import ProofPath
from .errors import MalformedMapProofError
from .optional_entry import OptionalEntry
from .branch_node import BranchNode
from ..hasher import Hasher
from ..utils import is_field_hash, to_bytes

# pylint: disable=C0103
logger = getLogger(__name__)


class _MapProofEntry:
    def __init__(self, path: ProofPath, data_hash: Hash):
        self.path = path
        self.hash = data_hash

    def __repr__(self) -> str:
        return "Entry [path: {}, hash: {}]".format(self.path, self.hash)

    @staticmethod
    def parse(data: Dict[str, str]) -> "_MapProofEntry":
        """ Parses MapProofEntry from the provided dict. """

        if not isinstance(data.get("path"), str) or not is_field_hash(data, "hash"):
            err = MalformedMapProofError.malformed_entry(data)
            logger.warning(str(err))
            raise err

        path_bits = data["path"]
        path = ProofPath.parse(path_bits)

        data_hash = to_bytes(data["hash"])
        if data_hash is None:
            err = MalformedMapProofError.malformed_entry(data)
            logger.warning(str(err))
            raise err

        return _MapProofEntry(path, Hash(data_hash))


def collect(entries: List[_MapProofEntry]) -> Hash:
    """
    Computes the root hash of the Merkle Patricia tree backing the specified entries
    in the map view.
    The tree is not restored in full; instead, we add the paths to
    the tree in their lexicographic order (i.e., according to the `PartialOrd` implementation
    of `ProofPath`) and keep track of the rightmost nodes (the right contour) of the tree.
    It is easy to see that adding paths in the lexicographic order means that only
    the nodes in the right contour may be updated on each step. Further, on each step
    zero or more nodes are evicted from the contour, and a single new node is
    added to it.
    `entries` are assumed to be sorted by the path in the increasing order.
    """

    def common_prefix(left: ProofPath, right: ProofPath) -> ProofPath:
        return left.prefix(left.common_prefix_len(right))

    def hash_branch(left_child: _MapProofEntry, right_child: _MapProofEntry) -> Hash:
        branch = BranchNode()
        branch.set_child("left", left_child.path, left_child.hash)
        branch.set_child("right", right_child.path, right_child.hash)

        return branch.object_hash()

    def fold(contour: List[_MapProofEntry], last_prefix: ProofPath) -> Optional[ProofPath]:
        last_entry = contour.pop()
        penultimate_entry = contour.pop()

        contour.append(_MapProofEntry(path=last_prefix, data_hash=hash_branch(penultimate_entry, last_entry)))

        if len(contour) > 1:
            penultimate_entry = contour[len(contour) - 2]
            return common_prefix(penultimate_entry.path, last_prefix)

        return None

    if not entries:
        return Hash(Hasher.DEFAULT_HASH)

    if len(entries) == 1:
        if not entries[0].path.is_leaf():
            err = MalformedMapProofError.non_terminal_node(entries[0].path)
            logger.warning(str(err))
            raise err

        return Hasher.hash_single_entry_map(entries[0].path.as_bytes(), entries[0].hash)

    # There is more than 1 entry.

    # Contour of entries to be folded into the result hash:
    contour: List[_MapProofEntry] = []

    # Initical contour state:
    first_entry, second_entry = entries[0], entries[1]
    last_prefix = common_prefix(first_entry.path, second_entry.path)
    contour = [first_entry, second_entry]

    # Process the rest of the entries:
    for entry in entries[2:]:
        new_prefix = common_prefix(contour[-1].path, entry.path)

        # Fold contour from the latest added entry to the beginning.
        # At each iteration take two latest entries and attempt to fold them into one new entry:
        while len(contour) > 1 and len(new_prefix) < len(last_prefix):
            prefix = fold(contour, last_prefix)
            if prefix is not None:
                last_prefix = prefix

        contour.append(entry)
        last_prefix = new_prefix

    # All entries are processed. Fold the contour into the final hash:
    while len(contour) > 1:
        prefix = fold(contour, last_prefix)
        if prefix:
            last_prefix = prefix

    logger.debug("Successfully computed the root hash of the Merkle Patricia tree.")
    return contour[0].hash


class CheckedMapProof:
    """ Version of `MapProof` obtained after verification. """

    def __init__(self, entries: List[OptionalEntry], root_hash: Hash):
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

    def root_hash(self) -> Hash:
        """ Returns a hash of the map for which this proof is constructed. """
        return self._root_hash


class MapProof:
    """
    Proof of existence for a map.

    This class is capable of parsing MapProof from Dict[Any, Any] and
    verifying the parsed proof.

    In most cases you do not need to create MapProof manually (use MapProofBuilder instead).

    However, if you understand that MapProofBuilder does not suit your needs, use the
    following workflow:

    >>> proof = get_proof_somehow()
    >>> # Assuming that the Protobuf files for the service are already loaded and compiled.
    >>> cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
    >>> cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')
    >>> cryptocurrency_decoder = MapProofBuilder.build_encoder_function(cryptocurrency_module.Wallet)
    >>> # Keys will be encoded to bytes using "bytes.fromhex",
    >>> # and values will be encoded using "Wallet" Protobuf structure.
    >>> parsed_proof = MapProof.parse(proof, lambda x: bytes.fromhex(x), cryptocurrency_decoder)
    >>> # CheckedMapProof will be returned.
    >>> result = parsed_proof.check()
    ```
    """

    def __init__(
        self,
        entries: List[OptionalEntry],
        proof: List[_MapProofEntry],
        key_to_bytes: Callable[[Any], bytes],
        value_to_bytes: Callable[[Any], bytes],
    ):
        """
        Constructor of MapProof. Do not call it directly, use `MapProof.parse`.
        """
        self.entries = entries
        self.proof = proof
        self._key_to_bytes = key_to_bytes
        self._value_to_bytes = value_to_bytes

    def __repr__(self) -> str:
        format_str = "MapProof [\n  Entries: {}\n  Proof: {}\n]\n"

        return format_str.format(self.entries, self.proof)

    @staticmethod
    def parse(
        data: Dict[str, Any], key_to_bytes: Callable[[Any], bytes], value_to_bytes: Callable[[Any], bytes]
    ) -> "MapProof":
        """
        Method to parse a proof.

        Example of the expected proof format:

        >>>
        {
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

        Parameters
        ----------
        data: Dict[str, Any]
            Name of the Protobuf structure to be used in the converted function.
        key_to_bytes: Callable[[Any], bytes]
            Function that will be used to convert keys to bytes.
        value_to_bytes: Callable[[Any], bytes]
            Function that will be used to convert values to bytes.

        Returns
        -------
        MapProof
            If parsing succeeds, MapProof object is returned.

        Raises
        ------
        MalformedMapProofError
            If provided raw MapProof is malformed and parsing fails, this exception
            rises.
        """

        if data.get("entries") is None or data.get("proof") is None:
            logger.warning("'entries' or 'proof' field is missing in the proof dictionary.")
            raise MalformedMapProofError.malformed_entry(data)

        entries: List[OptionalEntry] = [OptionalEntry.parse(raw_entry) for raw_entry in data["entries"]]
        proof: List[_MapProofEntry] = [_MapProofEntry.parse(raw_entry) for raw_entry in data["proof"]]

        map_proof = MapProof(entries, proof, key_to_bytes, value_to_bytes)
        logger.debug("Successfully built MapProof from the given proof dictionary.")
        return map_proof

    @staticmethod
    def _check_proof(proof: List[_MapProofEntry]) -> None:
        for idx in range(1, len(proof)):
            prev_path, path = proof[idx - 1].path, proof[idx].path

            if prev_path < path:
                if path.starts_with(prev_path):
                    err = MalformedMapProofError.embedded_paths(prev_path, path)
                    logger.warning(str(err))
                    raise err
            elif prev_path == path:
                err = MalformedMapProofError.duplicate_path(path)
                logger.warning(str(err))
                raise err
            elif prev_path > path:
                err = MalformedMapProofError.invalid_ordering(prev_path, path)
                logger.warning(str(err))
                raise err
            else:
                assert False, "Incomparable keys in the proof"

    def check(self) -> CheckedMapProof:
        """
        Calculates the root hash from the parsed proof.

        Returns
        -------
        CheckedMapProof
            If no errors occur during the calculation, a CheckedMapProof entity is returned.

        Raises
        ------
        MalformedMapProofError
            If provided raw MapProof is malformed and parsing fails, this exception
            rises.
        """

        def kv_to_map_entry(key_value: OptionalEntry) -> _MapProofEntry:
            key_bytes = self._key_to_bytes(key_value.key)
            key_hash = Hasher.hash_raw_data(key_bytes)

            path = ProofPath.from_bytes(key_hash.value)
            value_hash = Hasher.hash_leaf(self._value_to_bytes(key_value.value))

            return _MapProofEntry(path, value_hash)

        proof = self.proof[:]

        actual_entries = filter(lambda el: not el.is_missing, self.entries)

        proof += map(kv_to_map_entry, actual_entries)

        proof.sort(key=lambda el: el.path)

        self._check_proof(proof)

        result = collect(proof)

        return CheckedMapProof(self.entries, Hasher.hash_map_node(result))
