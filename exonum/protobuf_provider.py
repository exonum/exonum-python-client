"""Protobuf sources provider module."""

from typing import Dict, Optional, List
import re
import os
import requests

from exonum.protobuf_loader import ProtobufProviderInterface, ProtoFile


class _GithubProtobufProvider(ProtobufProviderInterface):

    GITHUB_URL_REGEX = re.compile(
        r"https://github.com/(?P<organization>[\w.-]+)/(?P<repo>[\w.-]+)/tree/(?P<ref>[\w.-]+)/(?P<path>.+)"
    )

    def __init__(self, service_name: Optional[str], github_folder_path: str) -> None:
        match = self.GITHUB_URL_REGEX.match(github_folder_path)

        if not match:
            raise RuntimeError(f"Invalid github folder path: {github_folder_path}")

        self._organization = match.group("organization")
        self._repo = match.group("repo")
        self._ref = match.group("ref")
        self._path = match.group("path")
        self._is_main = not service_name  # True if None is provided.
        if not self._is_main:
            self._service_name = service_name

    def get_main_proto_sources(self) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        if not self._is_main:
            raise RuntimeError("Attempt to get main sources from source github repo")

        return self._get_sources()

    def get_proto_sources_for_artifact(self, runtime_id: int, artifact_name: str) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        if self._is_main or self._service_name != artifact_name:
            raise RuntimeError("Attempt to get sources for wrong artifact")

        return self._get_sources()

    def _get_sources(self) -> List[ProtoFile]:
        content_url = (
            f"https://api.github.com/repos/{self._organization}/{self._repo}/contents/{self._path}?ref={self._ref}"
        )

        content = requests.get(content_url)

        result: List[ProtoFile] = []

        for source_file in content.json():
            name = source_file["name"]
            if not name.endswith(".proto"):
                continue
            file_content = requests.get(source_file["download_url"]).content.decode("utf-8")

            result.append(ProtoFile(name=name, content=file_content))

        return result


class _FilesystemProtobufProvider(ProtobufProviderInterface):
    def __init__(self, service_name: Optional[str], folder_path: str) -> None:
        if not os.path.isdir(folder_path):
            raise ValueError(f"Incorrect protobuf sources path: {folder_path}")

        self._path = folder_path
        self._is_main = not service_name  # True if None is provided.
        if not self._is_main:
            self._service_name = service_name

    def get_main_proto_sources(self) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        if not self._is_main:
            raise RuntimeError("Attempt to get main sources from source github repo")

        return self._get_sources()

    def get_proto_sources_for_artifact(self, runtime_id: int, artifact_name: str) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        if self._is_main or self._service_name != artifact_name:
            raise RuntimeError("Attempt to get sources for wrong artifact")

        return self._get_sources()

    def _get_sources(self) -> List[ProtoFile]:
        result: List[ProtoFile] = []

        for name in os.listdir(self._path):
            if not name.endswith(".proto"):
                continue

            with open(os.path.join(self._path, name), "r") as proto_file:
                file_content = proto_file.read()

            result.append(ProtoFile(name=name, content=file_content))

        return result


class ProtobufProvider(ProtobufProviderInterface):
    """Protobuf Provider class.

    It supports two types of receiving protobuf sources:

    - via filesystem,
    - via `github`.

    # TODO explain more.
    """

    def __init__(self) -> None:
        """Constructor of the ProtobufProvider class."""
        self._lookup: Dict[str, ProtobufProviderInterface] = dict()

    def add_source(self, source_path: str, service_name: Optional[str] = None) -> None:
        """Adds a source into ProtobufProvider.

        Examples:

        >>> provider = ProtobufProvider()
        >>> main_sources_path = "https://github.com/exonum/exonum/tree/master/exonum/src/proto/schema/exonum"
        >>> service_sources_path = "/home/user/service/proto_dir"
        >>> provider.add_source(main_sources_path) # Add main sources from github.
        >>> provider.add_source(service_sources_path, "service_name") # Add service sources from local folder.
        """
        if not service_name:
            verbose_service_name = "_main"
        else:
            verbose_service_name = service_name

        if self._lookup.get(verbose_service_name):
            raise ValueError("Duplicate source")

        if os.path.isdir(source_path):
            self._lookup[verbose_service_name] = _FilesystemProtobufProvider(service_name, source_path)
        elif source_path.startswith("https://github.com"):
            self._lookup[verbose_service_name] = _GithubProtobufProvider(service_name, source_path)
        else:
            raise ValueError(f"Incorrect source path: {source_path}")

    def get_main_proto_sources(self) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        if not self._lookup.get("_main"):
            raise RuntimeError("Main sources provider is not set")

        return self._lookup["_main"].get_main_proto_sources()

    def get_proto_sources_for_artifact(self, runtime_id: int, artifact_name: str) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        if not self._lookup.get(artifact_name):
            raise RuntimeError(f"Souce provider for service '{artifact_name}' is not set.'")

        return self._lookup[artifact_name].get_proto_sources_for_artifact(runtime_id, artifact_name)
