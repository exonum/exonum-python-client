"""Protobuf Example"""
from exonum.protobuf_provider import ProtobufProvider
from exonum import ExonumClient, ModuleManager

RUST_RUNTIME_ID = 0


def cryptocurrency_advanced_protobuf_provider() -> ProtobufProvider:
    """Creates a protobuf provider with main protobuf sources and cryptocurrency-advanced sources for v0.12"""
    main_sources_url = "https://github.com/exonum/exonum/tree/v0.12/exonum/src/proto/schema/exonum"
    cryptocurrency_sources_url = (
        "https://github.com/exonum/exonum/tree/v0.12/examples/cryptocurrency-advanced/backend/src/proto"
    )
    protobuf_provider = ProtobufProvider()
    protobuf_provider.add_source(main_sources_url)
    protobuf_provider.add_source(cryptocurrency_sources_url, "cryptocurrency-advanced")

    return protobuf_provider


def run() -> None:
    """Example of downloading the Protobuf sources and using the compiled
    module."""

    # Setup protobuf provider.
    protobuf_provider = cryptocurrency_advanced_protobuf_provider()

    # Create client.
    client = ExonumClient(hostname="127.0.0.1", public_api_port=8080, private_api_port=8081)
    client.set_protobuf_provider(protobuf_provider)

    # Create ProtobufLoader via context manager (so that we will not have to
    # initialize/deinitialize it manually):
    with client.protobuf_loader() as loader:
        # Load core proto files:
        loader.load_main_proto_files()
        # Load proto files for the Exonum supervisor service:
        loader.load_service_proto_files(RUST_RUNTIME_ID, "cryptocurrency-advanced")

        # Load the main module (helpers.proto).
        helpers_module = ModuleManager.import_main_module("helpers")

        # Create a Protobuf message object:
        public_key = helpers_module.PublicKey()
        public_key.data = bytes([i for i in range(32)])

        # Load the service module (cryptocurrency.proto from the cryptocurrency-advanced service).
        service_module = ModuleManager.import_service_module("cryptocurrency-advanced", "cryptocurrency")
        # Note that if we want to work with service module, we should use helpers also from that module.
        # That's required because of the inner python Protobuf implementation check system.
        cryptocurrency_helpers_module = ModuleManager.import_service_module("cryptocurrency-advanced", "helpers")

        # Workflow is the same as for the main modules:
        transfer = service_module.Transfer()
        cryptocurrency_public_key = cryptocurrency_helpers_module.PublicKey()
        cryptocurrency_public_key.data = bytes([i for i in range(32)])

        # Working with Protobuf objects, you have to follow Protobuf Python API conventions.
        # See Protobuf Python API docs for details.
        transfer.to.CopyFrom(cryptocurrency_public_key)
        transfer.amount = 10
        transfer.seed = 1


if __name__ == "__main__":
    run()
