import shutil
import sys
import os
import tempfile
import re

from .protoc import Protoc
from .errors import ProtobufLoaderEntityExists


class ProtobufLoader:
    entity = None

    def __init__(self, client):
        # TODO add a warning that object should be created via "with".
        if ProtobufLoader.entity is not None:
            raise ProtobufLoaderEntityExists("There is already a ProtobufLoader entity created")

        ProtobufLoader.entity = self
        self.client = client
        self.protoc = Protoc()
        self.proto_dir = None

    def __enter__(self):
        self.initialize()

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.deinitialize()

    def initialize(self):
        # Create directory for temporary files.
        self.proto_dir = tempfile.mkdtemp(prefix="exonum_client_")

        # Create folder for python files output.
        python_modules_path = os.path.join(self.proto_dir, "exonum_modules")
        os.makedirs(python_modules_path)

        # Create __init__ file in the exonum_modules directory.
        init_file_path = os.path.join(python_modules_path, "__init__.py")
        open(init_file_path, "a").close()

        # Add directory with exonum_modules into python path.
        sys.path.append(self.proto_dir)

    def deinitialize(self):
        # Mark entity as removed.
        ProtobufLoader.entity = None

        # Remove generated temporary directory.
        sys.path.remove(self.proto_dir)
        shutil.rmtree(self.proto_dir)

    def _save_proto_file(self, path, file_content):
        with open(path, "wt") as file_out:
            file_out.write(file_content)

    def _save_files(self, path, files):
        os.makedirs(path)
        for proto_file in files:
            file_name = proto_file["name"]
            file_content = proto_file["content"]
            file_path = os.path.join(path, file_name)
            self._save_proto_file(file_path, file_content)

    def load_main_proto_files(self):
        # TODO error handling

        # This method is not intended to be used by the end users, but it's OK to call it here.
        # pylint: disable=protected-access
        proto_contents = self.client._get_main_proto_sources().json()

        # Save proto_sources in proto/main directory.
        main_dir = os.path.join(self.proto_dir, "proto", "main")
        self._save_files(main_dir, proto_contents)

        # Call protoc to compile proto sources.
        proto_dir = os.path.join(self.proto_dir, "exonum_modules", "main")
        self.protoc.compile(main_dir, proto_dir)

    def load_service_proto_files(self, runtime_id, service_name):
        # TODO error handling

        # This method is not intended to be used by the end users, but it's OK to call it here.
        # pylint: disable=protected-access
        proto_contents = self.client._get_proto_sources_for_artifact(runtime_id, service_name).json()

        # Save proto_sources in proto/service_name directory.
        service_module_name = re.sub(r"[-. :/]", "_", service_name)
        service_dir = os.path.join(self.proto_dir, "proto", service_module_name)
        self._save_files(service_dir, proto_contents)

        # Call protoc to compile proto sources.
        main_dir = os.path.join(self.proto_dir, "proto", "main")
        proto_dir = os.path.join(self.proto_dir, "exonum_modules", service_module_name)
        self.protoc.compile(service_dir, proto_dir, include=main_dir)
