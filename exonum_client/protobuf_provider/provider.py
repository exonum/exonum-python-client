"""Protobuf sources provider module."""

from typing import Dict, List
import os

from exonum_client.protobuf_loader import ProtobufProviderInterface, ProtoFile
from exonum_client.protobuf_provider.github import _GithubProtobufProvider
from exonum_client.protobuf_provider.filesystem import _FilesystemProtobufProvider


class ProtobufProvider(ProtobufProviderInterface):
    """Protobuf Provider class.

    It supports two types of receiving protobuf sources:

    - via filesystem,
    - via `github`,
    - via external "fallback" providers.

    This class is designed to obtain required Protobuf sources from different places.
    For each service, user is able to add source from which `.proto` files will be obtained.

    If for some request there will be no source set, `ProtobufProvider` will try to use
    a "fallback" provider, specific to the runtime.

    E.g., for the Rust runtime, sources will be obtained from the REST API provided by the Exonum Rust
    runtime API.

    If there is no fallback provider for the request's runtime, an exception will be raised.

    # TODO explain more.
    """

    RUST_RUNTIME_ID = 0

    def __init__(self) -> None:
        """Constructor of the ProtobufProvider class."""
        self._lookup: Dict[str, ProtobufProviderInterface] = dict()
        self._fallback: Dict[int, ProtobufProviderInterface] = dict()

    def add_fallback_provider(self, runtime_id: int, fallback_probider: ProtobufProviderInterface) -> None:
        """Adds a provider which will be used if provider for required service
        was not found.
        """

        self._fallback[runtime_id] = fallback_probider

    def add_main_source(self, source_path: str) -> None:
        """Adds a main source for common Exonum protobuf files.

        Note that currently there is no need to provide "main" source separately, since Exonum
        node can provide them via API.
        """

        # Main sources will be stored in the lookup table as "_main_".
        self.add_service_source(source_path, "_main", "")

    def add_service_source(self, source_path: str, service_name: str, service_version: str) -> None:
        """Adds a source for Exonum service into ProtobufProvider.

        A source must be either a filesystem path, or a GitHub url.

        Examples:

        >>> provider = ProtobufProvider()
        >>> main_sources_path = "https://github.com/exonum/exonum/tree/master/exonum/src/proto/schema/exonum"
        >>> service_sources_path = "/home/user/service/proto_dir"
        >>> provider.add_source(main_sources_path) # Add main sources from github.
        >>> provider.add_source(service_sources_path, "service_name") # Add service sources from local folder.
        """
        verbose_service_name = f"{service_name}_{service_version}"

        if self._lookup.get(verbose_service_name):
            raise ValueError("Duplicate source")

        if os.path.isdir(source_path):
            self._lookup[verbose_service_name] = _FilesystemProtobufProvider(service_name, service_version, source_path)
        elif source_path.startswith("https://github.com"):
            self._lookup[verbose_service_name] = _GithubProtobufProvider(service_name, service_version, source_path)
        else:
            raise ValueError(f"Incorrect source path: {source_path}")

    def get_main_proto_sources(self) -> List[ProtoFile]:
        """Gets the Exonum core proto sources."""
        provider = self._lookup.get("_main_")
        if provider is None:
            rust_runtime_provider = self._fallback.get(self.RUST_RUNTIME_ID)
            if rust_runtime_provider is None:
                raise RuntimeError(
                    "Main sources provider is not set and \
                     Rust runtime provider is not available"
                )

            provider = rust_runtime_provider

        return provider.get_main_proto_sources()

    def get_proto_sources_for_artifact(
        self, runtime_id: int, artifact_name: str, artifact_version: str
    ) -> List[ProtoFile]:
        """Gets the Exonum service proto sources."""
        verbose_service_name = f"{artifact_name}_{artifact_version}"
        provider = self._lookup.get(verbose_service_name)
        if provider is None:
            fallback_provider = self._fallback.get(runtime_id)
            if fallback_provider is None:
                raise RuntimeError(
                    f"Souce provider for service '{artifact_name}' is not set, \
                    and there is no fallback provider for runtime '{runtime_id}'"
                )

            provider = fallback_provider

        return provider.get_proto_sources_for_artifact(runtime_id, artifact_name, artifact_version)
