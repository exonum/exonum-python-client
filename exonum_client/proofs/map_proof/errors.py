"""Common Errors for the MapProof Module."""
from typing import Dict, Any
from enum import Enum, auto as enum_auto

from .constants import KEY_SIZE

# Methods are self-documenting here.
# pylint: disable=missing-docstring


class MalformedMapProofError(Exception):
    """Error to be raised if the provided proof is malformed."""

    class ErrorKind(Enum):
        """Kind of the error."""

        EMBEDDED_PATH = enum_auto()
        DUPLICATE_PATH = enum_auto()
        INVALID_ORDERING = enum_auto()
        NON_TERMINAL_NODE = enum_auto()
        MALFORMED_ENTRY = enum_auto()
        INVALID_KEY_SIZE = enum_auto()

    def __init__(self, message: str, error_data: Dict[str, Any]) -> None:
        super().__init__(message)

        self.error_data = error_data

    @classmethod
    def embedded_paths(cls, prefix: Any, path: Any) -> "MalformedMapProofError":
        error_msg = "Embedded path: prefix {}, path {}".format(prefix, path)
        error_data = {"kind": cls.ErrorKind.EMBEDDED_PATH, "prefix": prefix, "path": path}

        return cls(error_msg, error_data)

    @classmethod
    def duplicate_path(cls, path: Any) -> "MalformedMapProofError":
        error_msg = "Duplicate path: path {}".format(path)
        error_data = {"kind": cls.ErrorKind.DUPLICATE_PATH, "path": path}

        return cls(error_msg, error_data)

    @classmethod
    def invalid_ordering(cls, path_a: Any, path_b: Any) -> "MalformedMapProofError":
        error_msg = "Invalid ordering: prev_path {}, path {}".format(path_a, path_b)
        error_data = {"kind": cls.ErrorKind.INVALID_ORDERING, "prev_path": path_a, "path": path_b}

        return cls(error_msg, error_data)

    @classmethod
    def non_terminal_node(cls, node: Any) -> "MalformedMapProofError":
        error_msg = "Non-terminal node: node {}".format(node)
        error_data = {"kind": cls.ErrorKind.NON_TERMINAL_NODE, "node": node}

        return cls(error_msg, error_data)

    @classmethod
    def malformed_entry(cls, entry: Any, additional_info: Any = None) -> "MalformedMapProofError":
        error_msg = "Malformed proof entry: entry {}".format(entry)
        if additional_info:
            error_msg += " [{}]".format(additional_info)
        error_data = {"kind": cls.ErrorKind.MALFORMED_ENTRY, "entry": entry}

        return cls(error_msg, error_data)

    @classmethod
    def invalid_key_size(cls, key: bytes) -> "MalformedMapProofError":
        error_msg = f"Invalid key '{key!r}' for raw MapProof, expected size {KEY_SIZE}, actual {len(key)}"

        error_data = {"kind": cls.ErrorKind.INVALID_KEY_SIZE, "key": key}

        return cls(error_msg, error_data)


class MapProofBuilderError(Exception):
    """Error that can occur in MapProofBuilder."""

    def __init__(self, msg: str, error_data: Any = None) -> None:
        super().__init__(msg)

        self.error_data = error_data
