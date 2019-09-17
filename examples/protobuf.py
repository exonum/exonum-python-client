"""Protobuf example"""
from exonum import ExonumClient, ModuleManager

RUST_RUNTIME_ID = 0


def run() -> None:
    """Example of downloading the protobuf sources and using the compiled module."""
    client = ExonumClient(hostname="127.0.0.1", public_api_port=8080, private_api_port=8081)

    # Create ProtobufLoader via context manager (so we won't have to initialize/deinitialize it manually).
    with client.protobuf_loader() as loader:
        # Load core proto files.
        loader.load_main_proto_files()
        # Load proto files for Exonum supervisor service.
        loader.load_service_proto_files(RUST_RUNTIME_ID, "exonum-supervisor:0.12.0")

        # Load main module (runtime.proto).
        main_module = ModuleManager.import_main_module("runtime")

        # Create a Protobuf message object.
        artifact_id = main_module.ArtifactId()
        artifact_id.runtime_id = RUST_RUNTIME_ID
        artifact_id.name = "some_service:0.1.0"

        # Working with Protobuf objects, you have to follow Protobuf Python API conventions.
        # See Protobuf Python API docs for details.
        instance_spec = main_module.InstanceSpec()
        instance_spec.artifact.CopyFrom(artifact_id)

        # Load service module (service.proto from supervisor service).
        service_module = ModuleManager.import_service_module("exonum-supervisor:0.12.0", "service")

        # Workflow is the same as for main modules.
        _deploy_request = service_module.DeployRequest()


if __name__ == "__main__":
    run()
