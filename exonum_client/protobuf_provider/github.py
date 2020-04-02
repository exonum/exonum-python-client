"""Protobuf provider which loads .proto files from GitHub."""

import os
import re
from typing import List
import requests

from exonum_client.protobuf_loader import ProtobufProviderInterface, ProtoFile


class _GithubProtobufProvider(ProtobufProviderInterface):

    GITHUB_URL_REGEX = re.compile(
        r"https://github.com/(?P<organization>[\w.-]+)/(?P<repo>[\w.-]+)/tree/(?P<ref>[\w.-]+)/(?P<path>.+)"
    )

    def __init__(self, service_name: str, service_version: str, github_folder_path: str) -> None:
        match = self.GITHUB_URL_REGEX.match(github_folder_path)

        if not match:
            raise RuntimeError(f"Invalid github folder path: {github_folder_path}")

        self._organization = match.group("organization")
        self._repo = match.group("repo")
        self._ref = match.group("ref")
        self._path = match.group("path")
        self._is_main = service_name == "_main"
        if not self._is_main:
            self._service_name = service_name
            self._service_version = service_version

    def get_main_proto_sources(self) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        if not self._is_main:
            raise RuntimeError("Attempt to get main sources from source specified as service")

        return self._get_sources()

    def get_proto_sources_for_artifact(
        self, runtime_id: int, artifact_name: str, artifact_version: str
    ) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        if self._is_main or self._service_name != artifact_name or self._service_version != artifact_version:
            raise RuntimeError("Attempt to get sources for wrong artifact")

        return self._get_sources()

    def _get_sources(self) -> List[ProtoFile]:
        results: List[ProtoFile] = []
        self._get_sources_recursive(self._path, results)

        return results

    def _get_sources_recursive(self, path: str, results: List[ProtoFile]) -> None:
        content_url = f"https://api.github.com/repos/{self._organization}/{self._repo}/contents/{path}?ref={self._ref}"

        content = requests.get(content_url)

        for source_file in content.json():
            _name = source_file["name"]
            _type = source_file["type"]

            if _type == "file" and _name.endswith(".proto"):
                file_content = requests.get(source_file["download_url"]).content.decode("utf-8")
                full_name = os.path.join(path.replace("src/", ""), _name) if self._is_main else _name
                results.append(ProtoFile(name=full_name, content=file_content))

            if _type == "dir":
                _path = source_file["path"]
                self._get_sources_recursive(_path, results)
