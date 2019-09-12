from enum import Enum, auto as enum_auto


class MalformedMapProofError(Exception):
    class ErrorKind(Enum):
        EMBEDDED_PATH = enum_auto()
        DUPLICATE_PATH = enum_auto()
        INVALID_ORDERING = enum_auto()
        NON_TERMINAL_NODE = enum_auto()
        MALFORMED_ENTRY = enum_auto()

    def __init__(self, message, error_data):
        super().__init__(message)

        self.error_data = error_data

    @classmethod
    def embedded_paths(cls, prefix, path) -> "MalformedMapProofError":
        error_msg = "Embedded path: prefix {}, path {}".format(prefix, path)
        error_data = {"kind": cls.ErrorKind.EMBEDDED_PATH, "prefix": prefix, "path": path}

        return cls(error_msg, error_data)

    @classmethod
    def duplicate_path(cls, path) -> "MalformedMapProofError":
        error_msg = "Duplicate path: path {}".format(path)
        error_data = {"kind": cls.ErrorKind.DUPLICATE_PATH, "path": path}

        return cls(error_msg, error_data)

    @classmethod
    def invalid_ordering(cls, path_a, path_b) -> "MalformedMapProofError":
        error_msg = "Invalid ordering: prev_path {}, path {}".format(path_a, path_b)
        error_data = {"kind": cls.ErrorKind.INVALID_ORDERING, "prev_path": path_a, "path": path_b}

        return cls(error_msg, error_data)

    @classmethod
    def non_terminal_node(cls, node) -> "MalformedMapProofError":
        error_msg = "Non-terminal node: node {}".format(node)
        error_data = {"kind": cls.ErrorKind.NON_TERMINAL_NODE, "node": node}

        return cls(error_msg, error_data)

    @classmethod
    def malformed_entry(cls, entry, additional_info=None) -> "MalformedMapProofError":
        error_msg = "Malformed proof entry: entry {}".format(entry)
        if additional_info:
            error_msg += " [{}]".format(additional_info)
        error_data = {"kind": cls.ErrorKind.MALFORMED_ENTRY, "entry": entry}

        return cls(error_msg, error_data)


class MapProofBuilderError(Exception):
    def __init__(self, msg, error_data=None):
        super().__init__(msg)

        self.error_data = error_data
