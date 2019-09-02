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
    def embedded_paths(cls, prefix, path) -> 'MalformedMapProofError':
        error_msg = 'embedded path: prefix {}, path {}'.format(prefix, path)
        error_data = {'kind': cls.ErrorKind.EMBEDDED_PATH, 'prefix': prefix, 'path': path}

        return cls(error_msg, error_data)

    @classmethod
    def duplicate_path(cls, path) -> 'MalformedMapProofError':
        error_msg = 'duplicate path: path {}'.format(path)
        error_data = {'kind': cls.ErrorKind.DUPLICATE_PATH, 'path': path}

        return cls(error_msg, error_data)

    @classmethod
    def invalid_ordering(cls, prev_path, path) -> 'MalformedMapProofError':
        error_msg = 'embedded path: prev_path {}, path {}'.format(prev_path, path)
        error_data = {'kind': cls.ErrorKind.INVALID_ORDERING, 'prev_path': prev_path, 'path': path}

        return cls(error_msg, error_data)

    @classmethod
    def non_terminal_node(cls, node) -> 'MalformedMapProofError':
        error_msg = 'non-terminal node: node {}'.format(node)
        error_data = {'kind': cls.ErrorKind.NON_TERMINAL_NODE, 'node': node}

        return cls(error_msg, error_data)

    @classmethod
    def malformed_entry(cls, entry, additional_info=None) -> 'MalformedMapProofError':
        error_msg = 'malformed proof entry: entry {}'.format(entry)
        if additional_info:
            error_msg += ' [{}]'.format(additional_info)
        error_data = {'kind': cls.ErrorKind.MALFORMED_ENTRY, 'entry': entry}

        return cls(error_msg, error_data)