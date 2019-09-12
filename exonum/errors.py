"""Module with the common Exonum errors."""


class ProtobufLoaderEntityExists(Exception):
    """Error to be raised if there was an attempt to create more than one entity of the ProtobufLoader."""
