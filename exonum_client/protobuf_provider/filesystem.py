"""Protobuf provider which loads .proto files from the filesystem."""

import glob
import os
from typing import List

from exonum_client.protobuf_loader import ProtobufProviderInterface, ProtoFile


class _FilesystemProtobufProvider(ProtobufProviderInterface):
    def __init__(self, service_name: str, service_version: str, folder_path: str) -> None:
        if not os.path.isdir(folder_path):
            raise ValueError(f"Incorrect protobuf sources path: {folder_path}")

        self._path = folder_path
        self._is_main = service_name == "_main"
        if not self._is_main:
            self._service_name = service_name
            self._service_version = service_version

    def get_main_proto_sources(self) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        if not self._is_main:
            raise RuntimeError("Attempt to get main sources from filesystem source.")

        return self._get_sources()

    def get_proto_sources_for_artifact(
        self, runtime_id: int, artifact_name: str, artifact_version: str
    ) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        if self._is_main or self._service_name != artifact_name or self._service_version != artifact_version:
            raise RuntimeError("Attempt to get sources for wrong artifact")

        return self._get_sources()

    def _get_sources(self) -> List[ProtoFile]:
        result: List[ProtoFile] = []

        for name in glob.glob(self._path + "/**/*.proto", recursive=True):
            with open(name, "r") as proto_file:
                file_content = proto_file.read()

            result.append(ProtoFile(name=os.path.relpath(name, self._path), content=file_content))

        return result
