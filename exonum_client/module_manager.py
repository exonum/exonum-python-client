"""Module capable of loading the Protobuf-generated modules."""
from typing import Any
import importlib
import re


class ModuleManager:
    """ModuleManager class provides an interface for importing modules generated from the previously downloaded
    Protobuf sources.

    It is supposed that you call those methods only after downloading the corresponding module via ProtobufLoader.
    Otherwise an error will be raised.

    Example usage:

    >>> with client.protobuf_loader() as loader:
    >>>     loader.load_main_proto_files()
    >>>     loader.load_service_proto_files(0, "exonum-supervisor:0.13.0-rc.2")
    >>>     main_module = ModuleManager.import_main_module("runtime")
    >>>     service_module = ModuleManager.import_service_module("exonum-supervisor:0.13.0-rc.2", "service")
    """

    @staticmethod
    def import_main_module(module_name: str) -> Any:
        """Imports the main (used by the Exonum core) module, e.g. "consensus", "runtime", etc."""
        module = importlib.import_module("exonum_modules.main.{}_pb2".format(module_name))

        return module

    @staticmethod
    def import_service_module(artifact_name: str, module_name: str) -> Any:
        """Imports the service (corresponding to some artifact) module."""
        artifact_module_name = re.sub(r"[-. :/]", "_", artifact_name)
        module = importlib.import_module("exonum_modules.{}.{}_pb2".format(artifact_module_name, module_name))

        return module
