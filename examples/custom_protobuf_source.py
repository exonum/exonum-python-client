"""Custom Protobuf Source Example.

This example shows how to use Exonum Python light client with custom protobuf sources.
In this file, we will make light client compile protobuf sources for version 0.12 (instead
of actual one).

Though this may be not really useful (since light client itself is not compatible with Exonum
0.12), it can be extrapolated to other use cases, e.g. work with other runtimes that do not
support obtaining protobuf sources from REST API.
"""
from exonum_client.protobuf_provider import ProtobufProvider
from exonum_client import ExonumClient, ModuleManager

RUST_RUNTIME_ID = 0
SERVICE_VERSION = "0.12"


def setup_protobuf_provider(protobuf_provider: ProtobufProvider) -> None:
    """Setups a protobuf provider with main protobuf sources and cryptocurrency-advanced sources for v0.12.

    Exonum client creates a ProtobufProvider object during its initialization, so we take it here
    and just extend with new sources."""
    main_sources_url = "https://github.com/exonum/exonum/tree/v0.12/exonum/src/proto/schema/exonum"
    cryptocurrency_sources_url = (
        "https://github.com/exonum/exonum/tree/v0.12/examples/cryptocurrency-advanced/backend/src/proto"
    )
    protobuf_provider.add_main_source(main_sources_url)
    protobuf_provider.add_service_source(cryptocurrency_sources_url, "cryptocurrency-advanced", SERVICE_VERSION)


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
        loader.load_service_proto_files(RUST_RUNTIME_ID, "cryptocurrency-advanced", SERVICE_VERSION)

        # Load the main module (helpers.proto).
        helpers_module = ModuleManager.import_main_module("helpers")

        # Create a Protobuf message object:
        public_key = helpers_module.PublicKey()
        public_key.data = bytes(i for i in range(32))

        # Load the service module (cryptocurrency.proto from the cryptocurrency-advanced service).
        # Note that we load "cryptocurrency" module, which is absent in current version
        # of service, it only exists in Exonum 0.12.
        service_module = ModuleManager.import_service_module(
            "cryptocurrency-advanced", SERVICE_VERSION, "cryptocurrency"
        )
        # Note that if we want to work with service module, we should use helpers also from that module.
        # That's required because of the inner python Protobuf implementation check system.
        cryptocurrency_helpers_module = ModuleManager.import_service_module(
            "cryptocurrency-advanced", SERVICE_VERSION, "helpers"
        )

        # Workflow is the same as for the main modules:
        transfer = service_module.Transfer()
        cryptocurrency_public_key = cryptocurrency_helpers_module.PublicKey()
        cryptocurrency_public_key.data = bytes(i for i in range(32))

        # Working with Protobuf objects, you have to follow Protobuf Python API conventions.
        # See Protobuf Python API docs for details.
        transfer.to.CopyFrom(cryptocurrency_public_key)
        transfer.amount = 10
        transfer.seed = 1


if __name__ == "__main__":
    run()
