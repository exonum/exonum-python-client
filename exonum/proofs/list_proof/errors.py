from enum import Enum, auto as enum_auto


class MalformedListProofError(Exception):
    """
    Error raised if proof is malformed.
    Every object of this class contains field `error_kind` which is a value of type ErrorKind.
    This value described the kind of occured error.
    See enum ErrorKind for the details.
    """
    class ErrorKind(Enum):
        """
        Kind of the error. Possible variants:
        - UNEXPECTED_LEAF: Proof contains a hash in a place where a value was expected.
        - UNEXPECTED_BRANCH: Proof contains a hash in the position which is impossible according to the list length.
        - REDUNDANT_HASH: There are redundant hashes in the proof: the hash of the underlying list can be calculated
            without some of them.
        - MISSING_HASH: Proof does not contain necessary information to compute the hash of the underlying list.
        - NON_EMPTY_PROOF: Non-empty proof for an empty list.
        - DUPLICATE_KEY: Same key is used more than once in the proof.
        """
        UNEXPECTED_LEAF = enum_auto()
        UNEXPECTED_BRANCH = enum_auto()
        REDUNDANT_HASH = enum_auto()
        MISSING_HASH = enum_auto()
        NON_EMPTY_PROOF = enum_auto()
        PARSE_ERROR = enum_auto()
        DUPLICATE_KEY = enum_auto()

    def __init__(self, message, error_kind):
        super().__init__(message)

        self.error_kind = error_kind

    @classmethod
    def unexpected_leaf(cls) -> 'MalformedListProofError':
        error_msg = 'Unexpected leaf'
        error_kind = cls.ErrorKind.UNEXPECTED_LEAF

        return cls(error_msg, error_kind)

    @classmethod
    def unexpected_branch(cls) -> 'MalformedListProofError':
        error_msg = 'Unexpected branch'
        error_kind = cls.ErrorKind.UNEXPECTED_BRANCH

        return cls(error_msg, error_kind)

    @classmethod
    def redundant_hash(cls) -> 'MalformedListProofError':
        error_msg = 'Redundant hash'
        error_kind = cls.ErrorKind.REDUNDANT_HASH

        return cls(error_msg, error_kind)

    @classmethod
    def missing_hash(cls) -> 'MalformedListProofError':
        error_msg = 'Missing hash'
        error_kind = cls.ErrorKind.MISSING_HASH

        return cls(error_msg, error_kind)

    @classmethod
    def non_empty_proof(cls) -> 'MalformedListProofError':
        error_msg = 'Non-empty proof'
        error_kind = cls.ErrorKind.NON_EMPTY_PROOF

        return cls(error_msg, error_kind)

    @classmethod
    def parse_error(cls, message) -> 'MalformedListProofError':
        error_msg = f'Parsing error: could not parse {message}'
        error_kind = cls.ErrorKind.PARSE_ERROR

        return cls(error_msg, error_kind)

    @classmethod
    def duplicate_key(cls) -> 'MalformedListProofError':
        error_msg = 'Duplicate key'
        error_kind = cls.ErrorKind.DUPLICATE_KEY

        return cls(error_msg, error_kind)


class ListProofVerificationError(Exception):
    """ Error raised when provided root hash doesn't match calculated one. """
    def __init__(self, provided_hash, calculated_hash):
        def _short_hash(hash_bytes: bytes):
            hash_str = hash_bytes.hex()
            return hash_str[:4] + ".." + hash_str[-4:]

        err_msg = "Unmatched root hash. Got: {}, expected {}"
        super().__init__(err_msg.format(_short_hash(provided_hash), _short_hash(calculated_hash)))
        self.provided_hash = provided_hash
        self.calculated_hash = calculated_hash
