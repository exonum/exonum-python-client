"""Custom Protobuf Source Example.

This example shows how to use Exonum Python light client with custom protobuf sources.
In this file, we will make light client compile protobuf sources for version 0.12 (instead
of actual one).

Though this may be not really useful (since light client itself is not compatible with Exonum
1.0.0), it can be extrapolated to other use cases, e.g. work with other runtimes that do not
support obtaining protobuf sources from REST API.
"""
from exonum_client.protobuf_provider import ProtobufProvider
from exonum_client import ExonumClient, ModuleManager

RUST_RUNTIME_ID = 0
SERVICE_NAME = "cryptocurrency-advanced"
SERVICE_VERSION = "0.2.0"


def setup_protobuf_provider(protobuf_provider: ProtobufProvider) -> None:
    """Setups a protobuf provider with main protobuf sources and cryptocurrency-advanced sources for v0.2.0.

    Exonum client creates a ProtobufProvider object during its initialization, so we take it here
    and just extend with new sources."""
    main_sources_url = "https://github.com/exonum/exonum-proto-sources/tree/master/src/exonum"
    cryptocurrency_sources_url = (
        "https://github.com/exonum/exonum/tree/v1.0.0/examples/cryptocurrency-advanced/backend/src/proto"
    )
    protobuf_provider.add_main_source(main_sources_url)
    protobuf_provider.add_service_source(cryptocurrency_sources_url, SERVICE_NAME, SERVICE_VERSION)


def run() -> None:
    """Example of downloading the Protobuf sources and using the compiled
    module."""

    # Create client.
    client = ExonumClient(hostname="127.0.0.1", public_api_port=8080, private_api_port=8081)

    # Setup protobuf provider.
    setup_protobuf_provider(client.protobuf_provider)

    # Create ProtobufLoader via context manager (so that we will not have to
    # initialize/deinitialize it manually):
    with client.protobuf_loader() as loader:
        # Load core proto files:
        loader.load_main_proto_files()
        # Load proto files for the Exonum supervisor service:
        loader.load_service_proto_files(RUST_RUNTIME_ID, SERVICE_NAME, SERVICE_VERSION)

        # Load the main module (exonum/crypto/type.proto).
        types_module = ModuleManager.import_main_module("exonum.crypto.types")

        # Create a Protobuf message object:
        public_key = types_module.PublicKey()
        public_key.data = bytes(i for i in range(32))

        # Load the service module (service.proto from the cryptocurrency-advanced service).
        # Note that we load "service" module, which is absent in current version
        # of the service, it only exists in Exonum 1.0.
        service_module = ModuleManager.import_service_module(
            SERVICE_NAME, SERVICE_VERSION, "service"
        )
        # Note that if we want to work with service module, we should use types also from that module.
        # That's required because of the inner python Protobuf implementation check system.
        types_module = ModuleManager.import_service_module(
            SERVICE_NAME, SERVICE_VERSION, "exonum.crypto.types"
        )

        # Workflow is the same as for the main modules:
        transfer = service_module.Transfer()
        to = types_module.Hash()
        to.data = bytes(i for i in range(32))

        # Working with Protobuf objects, you have to follow Protobuf Python API conventions.
        # See Protobuf Python API docs for details.
        transfer.to.CopyFrom(to)
        transfer.amount = 10
        transfer.seed = 1


if __name__ == "__main__":
    run()
