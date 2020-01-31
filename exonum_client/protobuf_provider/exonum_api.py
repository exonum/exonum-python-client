"""This module introduces an ExonumApiProvider class, which is capable
of loading core protobuf files and protobuf files for Rust runtime via
Exonum node REST API.

This provider is enabled by default.
"""
from typing import Optional, Any, List, Dict

from logging import getLogger

from exonum_client.protobuf_loader import ProtoFile, ProtobufProviderInterface
from exonum_client.api import Api

# pylint: disable=C0103
logger = getLogger(__name__)


class ExonumApiProvider(Api, ProtobufProviderInterface):
    """ProtobufApi class implements ProtobufProviderInterface interface."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self._rust_runtime_url = self.endpoint_prefix + "/runtimes/rust/{}"

    def _get_proto_sources(self, params: Optional[Dict[str, str]] = None) -> List[ProtoFile]:
        """Retrieves protobuf sources."""
        proto_sources_endpoint = self._rust_runtime_url.format("proto-sources")
        response = self.get(proto_sources_endpoint, params=params)
        if response.status_code != 200 or "application/json" not in response.headers["content-type"]:
            logger.critical(
                "Unsuccessfully attempted to retrieve Protobuf sources.\n" "Status code: %s,\n" "body:\n%s",
                response.status_code,
                response.content,
            )
            raise RuntimeError("Unsuccessfully attempted to retrieve Protobuf sources: {!r}".format(response.content))
        logger.debug("Protobuf sources retrieved successfully.")

        proto_files = [
            ProtoFile(name=proto_file["name"], content=proto_file["content"]) for proto_file in response.json()
        ]

        return proto_files

    def get_main_proto_sources(self) -> List[ProtoFile]:
        """Performs a GET request to the `proto-sources` Exonum endpoint."""
        params = {"type": "core"}
        return self._get_proto_sources(params)

    def get_proto_sources_for_artifact(
        self, runtime_id: int, artifact_name: str, artifact_version: str
    ) -> List[ProtoFile]:
        """Raise an exception if runtime ID is not equal to the rust runtime ID."""
        if runtime_id != self.RUST_RUNTIME_ID:
            err_msg = f"Provided runtime ID: {runtime_id} is not equal to Rust runtime ID: {self.RUST_RUNTIME_ID}."
            logger.critical(err_msg)
            raise RuntimeError(err_msg)
        # Performs a GET request to the `proto-sources` Exonum endpoint with a provided artifact name:
        params = {"type": "artifact", "name": artifact_name, "version": artifact_version}

        return self._get_proto_sources(params)
