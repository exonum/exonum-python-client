"""Module containing the ProtobufLoader class, which is capable of downloading protobuf sources from the Exonum."""
from typing import List, Dict, Optional, Any, NamedTuple
import shutil
import sys
import os
import tempfile
import re

from .protoc import Protoc


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
    """ProtobufLoader is a class capable of loading and compiling protobuf sources from the Exonum.

    This class is a Singleton, meaning that there will be created only one entity of that class at the time.

    Example workflow:
    >>> with client.protobuf_loader() as loader:
    >>>    loader.load_main_proto_files()
    >>>    loader.load_service_proto_files(0, "exonum-supervisor:0.12.0")

    Code above will initialize loader, download core Exonum proto files and proto files for the Supervisor service,
    and compile them into python modules. After that you will be able to load those modules via ModuleManager.

    Please note that it's recommended to create ProtobufLoader object via context manager.
    Otherwise you will have to call `initialize` and `deinitialize` methods manually:

    >>> loader = client.protobuf_loader()
    >>> loader.initialize()
    >>> ... # Some code
    >>> loader.deinitialize()

    If you'll forget to call `deinitialize` (or if code will enter early, i.e. because of unhandled exception),
    recourses created in the temp folder (which may differ depending on your OS) will not be removed.

    Creating more than one entity at the same time will result in retrieving the same object:

    >>> with client.protobuf_loader() as loader_1:
    >>>     with client.protobuf_loader() as loader_2:
    >>>         assert loader_1 == loader_2

    This may be useful if you have several modules that should work with protobuf loader:
    >>> # main.py
    >>> loader = ProtobufLoader(client)
    >>> loader.initialize()
    >>> loader.load_main_proto_files()
    >>> ...
    >>> loader.deinitialize()

    >>> # module_a.py
    >>> loader = ProtobufLoader() # Since loader is already initialized with a client, you don't have to provide it.
    >>> loader.load_service_proto_files(runtime_a, service_a)

    >>> # module_b.py
    >>> loader = ProtobufLoader()
    >>> loader.load_service_proto_files(runtime_b, service_b)

    However, if you will try to create a second loader from client other than first, an ValueError will be raised.
    """

    _entity = None
    _reference_count = 0

    def __new__(cls, *_args: Any) -> "ProtobufLoader":
        # Check if entity is already created (and thus no new object should be created).
        if ProtobufLoader._entity is not None:
            return ProtobufLoader._entity

        # Create a new object.
        return super().__new__(cls)

    def __init__(self, client: Optional[ProtobufProviderInterface] = None):
        # Check that client is the same as expected.
        if ProtobufLoader._entity is not None:
            if client is not None and client != ProtobufLoader._entity.client:
                raise ValueError("Attempt to create ProtobufLoader entity with a different client")
            return

        if client is None:
            raise ValueError("Client is expected to be set for the initial object creation")

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

        # Update the reference counter.
        ProtobufLoader._reference_count += 1
        if ProtobufLoader._reference_count > 1:
            # If this is a second (third, etc) entity, everything is initialized already.
            return

        # Create directory for temporary files.
        self._proto_dir = tempfile.mkdtemp(prefix="exonum_client_")

        # Create folder for python files output.
        python_modules_path = os.path.join(self._proto_dir, "exonum_modules")
        os.makedirs(python_modules_path)

        # Create __init__ file in the exonum_modules directory.
        init_file_path = os.path.join(python_modules_path, "__init__.py")
        open(init_file_path, "a").close()

        # Add directory with exonum_modules into python path.
        sys.path.append(self._proto_dir)

    def deinitialize(self) -> None:
        """Performs a deinitialization process."""
        if self._proto_dir is None:
            raise RuntimeError("Attempt to deinitialize unititialized ProtobufLoader")

        # Decrement the reference counter.
        ProtobufLoader._reference_count -= 1

        # If there is more than one reference yet, nothing should be done.
        if ProtobufLoader._reference_count > 0:
            return

        # Mark entity as removed.
        ProtobufLoader._entity = None

        # Remove generated temporary directory.
        sys.path.remove(self._proto_dir)
        shutil.rmtree(self._proto_dir)

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
        """Loads and compiles main Exonum proto files."""
        if self._proto_dir is None:
            raise RuntimeError("Attempt to use unititialized ProtobufLoader")

        # This method is not intended to be used by the end users, but it's OK to call it here.
        # pylint: disable=protected-access
        proto_contents = self.client.get_main_proto_sources()

        # Save proto_sources in proto/main directory.
        main_dir = os.path.join(self._proto_dir, "proto", "main")
        self._save_files(main_dir, proto_contents)

        # Call protoc to compile proto sources.
        proto_dir = os.path.join(self._proto_dir, "exonum_modules", "main")
        self.protoc.compile(main_dir, proto_dir)

    def load_service_proto_files(self, runtime_id: int, service_name: str) -> None:
        """Loads and compiles proto files for a service."""
        if self._proto_dir is None:
            raise RuntimeError("Attempt to use unititialized ProtobufLoader")

        # This method is not intended to be used by the end users, but it's OK to call it here.
        # pylint: disable=protected-access
        proto_contents = self.client.get_proto_sources_for_artifact(runtime_id, service_name)

        # Save proto_sources in proto/service_name directory.
        service_module_name = re.sub(r"[-. :/]", "_", service_name)
        service_dir = os.path.join(self._proto_dir, "proto", service_module_name)
        self._save_files(service_dir, proto_contents)

        # Call protoc to compile proto sources.
        main_dir = os.path.join(self._proto_dir, "proto", "main")
        proto_dir = os.path.join(self._proto_dir, "exonum_modules", service_module_name)
        self.protoc.compile(service_dir, proto_dir, include=main_dir)
