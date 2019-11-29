"""Module Containing the ProtobufLoader Class.

ProtobufLoader is capable of downloading Protobuf sources from Exonum."""
from typing import List, Optional, Any, NamedTuple
from logging import getLogger
import shutil
import sys
import os
import tempfile
import re

from .protoc import Protoc

# pylint: disable=C0103
logger = getLogger(__name__)

PYTHON_RUNTIME = 2


class ProtoFile(NamedTuple):
    """Structure that represents a proto file."""

    name: str
    content: str


class ProtobufProviderInterface:
    """Interface for Protobuf sources provider."""

    def get_main_proto_sources(self) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        raise NotImplementedError

    def get_proto_sources_for_artifact(self, runtime_id: int, artifact_name: str) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        raise NotImplementedError


class ProtobufLoader:
    """ProtobufLoader is a class capable of loading and compiling Protobuf sources from Exonum.

    This class is a Singleton, meaning that only one entity of that class is created at a time.

    Example workflow:

    >>> with client.protobuf_loader() as loader:
    >>>    loader.load_main_proto_files()
    >>>    loader.load_service_proto_files(0, "exonum-supervisor:0.12.0")

    Code above will initialize loader, download core Exonum proto files and proto files for the Supervisor service.
    The code will compile the files into the Python modules. After that you will be able to load those modules
    via ModuleManager.

    Please note that it is recommended to create a ProtobufLoader object via the context manager.
    Otherwise you will have to call `initialize` and `deinitialize` methods manually:

    >>> loader = client.protobuf_loader()
    >>> loader.initialize()
    >>> ... # Some code
    >>> loader.deinitialize()

    If you forget to call `deinitialize` (or if the code exits earlier, for example because of unhandled exception),
    the recourses created in the temp folder (which may differ depending on your OS) will not be removed.

    Creating more than one entity at a time will result in retrieving the same object:

    >>> with client.protobuf_loader() as loader_1:
    >>>     with client.protobuf_loader() as loader_2:
    >>>         assert loader_1 == loader_2

    This may be useful if you have several modules that should work with ProtobufLoader:

    >>> # main.py
    >>> loader = ProtobufLoader(client)
    >>> loader.initialize()
    >>> loader.load_main_proto_files()
    >>> ...
    >>> loader.deinitialize()

    >>> # module_a.py
    >>> loader = ProtobufLoader() # Since loader is already initialized with the client, you do not have to provide it.
    >>> loader.load_service_proto_files(runtime_a, service_a)

    >>> # module_b.py
    >>> loader = ProtobufLoader()
    >>> loader.load_service_proto_files(runtime_b, service_b)

    However, if you try to create the second loader, different from the first one, from the client,
    ValueError will be raised.
    """

    _entity = None
    _reference_count = 0

    def __new__(cls, *_args: Any) -> "ProtobufLoader":
        # Check if the entity is already created (and thus no new object should be created):
        if ProtobufLoader._entity is not None:
            return ProtobufLoader._entity

        # Create a new object:
        return super().__new__(cls)

    def __init__(self, client: Optional[ProtobufProviderInterface] = None):
        # Check that the client is the same as expected:
        if ProtobufLoader._entity is not None:
            if client is not None and client != ProtobufLoader._entity.client:
                err_msg = (
                    f"Attempt to create ProtobufLoader entity with a different client:\n"
                    f"used client:\n{ProtobufLoader._entity.client}\n"
                    f"provided client:\n{client}\n"
                )
                logger.critical(err_msg)
                raise ValueError(err_msg)
            return

        if client is None:
            err_msg = "Client is expected to be set for the initial object creation."
            logger.critical(err_msg)
            raise ValueError(err_msg)

        ProtobufLoader._entity = self
        self.client = client
        self.protoc = Protoc()
        self._proto_dir: Optional[str] = None

    def __enter__(self) -> "ProtobufLoader":
        self.initialize()

        return self

    def __exit__(self, exc_type: Optional[type], exc_value: Optional[Any], exc_traceback: Optional[object]) -> None:
        self.deinitialize()

    def initialize(self) -> None:
        """Performs an initialization process."""

        # Update the reference counter:
        ProtobufLoader._reference_count += 1
        logger.debug("Current ProtobufLoader reference count: %s.", ProtobufLoader._reference_count)
        if ProtobufLoader._reference_count > 1:
            # If this is a second (third, etc) entity, everything is already initialized:
            return

        # Create a directory for temporary files:
        self._proto_dir = tempfile.mkdtemp(prefix="exonum_client_")

        # Create a folder for Python files output:
        python_modules_path = os.path.join(self._proto_dir, "exonum_modules")
        os.makedirs(python_modules_path)

        # Create __init__ file in the exonum_modules directory:
        init_file_path = os.path.join(python_modules_path, "__init__.py")
        open(init_file_path, "a").close()

        # Add a directory with exonum_modules into the Python path:
        sys.path.append(self._proto_dir)

        logger.debug("Successfully initialized ProtobufLoader for client:\n%s\n", self.client)

    def deinitialize(self) -> None:
        """Performs a deinitialization process."""
        if self._proto_dir is None:
            err_msg = "Attempt to deinitialize uninitialized ProtobufLoader."
            logger.critical(err_msg)
            raise RuntimeError(err_msg)

        # Decrement the reference counter:
        ProtobufLoader._reference_count -= 1
        logger.debug("Current ProtobufLoader reference count: %s.", ProtobufLoader._reference_count)

        # If there is at least one reference, nothing should be done:
        if ProtobufLoader._reference_count > 0:
            return

        # Mark entity as removed:
        ProtobufLoader._entity = None

        # Remove the generated temporary directory:
        sys.path.remove(self._proto_dir)
        shutil.rmtree(self._proto_dir)

        # Unload any previously loaded protobuf modules
        loaded_modules = list(sys.modules.keys())
        for module in loaded_modules:
            if module.startswith("exonum_modules"):
                del sys.modules[module]

        logger.debug("Successfully deinitialized ProtobufLoader.")

    @staticmethod
    def _save_proto_file(path: str, file_content: str) -> None:
        with open(path, "wt") as file_out:
            file_out.write(file_content)

    def _save_files(self, path: str, files: List[ProtoFile]) -> None:
        os.makedirs(path)
        for proto_file in files:
            file_path = os.path.join(path, proto_file.name)
            self._save_proto_file(file_path, proto_file.content)

    def load_main_proto_files(self) -> None:
        """Loads and compiles the main Exonum proto files."""
        if self._proto_dir is None:
            err_msg = "Attempt to use uninitialized ProtobufLoader."
            logger.critical(err_msg)
            raise RuntimeError(err_msg)

        # This method is not intended to be used by end users, but it is OK to call it here.
        # pylint: disable=protected-access
        proto_contents = self.client.get_main_proto_sources()

        # Save proto_sources in the proto/main directory:
        main_dir = os.path.join(self._proto_dir, "proto", "main")
        self._save_files(main_dir, proto_contents)

        # Call protoc to compile proto sources:
        proto_dir = os.path.join(self._proto_dir, "exonum_modules", "main")
        self.protoc.compile(main_dir, proto_dir)

    def load_service_proto_files(self, runtime_id: int, service_name: str) -> None:
        """Loads and compiles proto files for a service."""
        if self._proto_dir is None:
            logger.critical("Attempt to use unititialized ProtobufLoader.")
            raise RuntimeError("Attempt to use unititialized ProtobufLoader")

        # This method is not intended to be used by end users, but it is OK to call it here.
        # pylint: disable=protected-access
        proto_contents = self.client.get_proto_sources_for_artifact(runtime_id, service_name)

        # Save proto_sources in proto/service_name directory:
        service_module_name = re.sub(r"[-. :/]", "_", service_name)
        service_dir = os.path.join(self._proto_dir, "proto", service_module_name)
        self._save_files(service_dir, proto_contents)

        # Call protoc to compile proto sources:
        main_dir = os.path.join(self._proto_dir, "proto", "main")
        proto_dir = os.path.join(self._proto_dir, "exonum_modules", service_module_name)
        if runtime_id != PYTHON_RUNTIME:
            self.protoc.compile(service_dir, proto_dir, include=main_dir)
        else:
            # Python services do not rely on the `includes` from the exonum core.
            self.protoc.compile(service_dir, proto_dir)
