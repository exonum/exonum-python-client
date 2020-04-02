"""Protobuf Example"""
from exonum_client import ExonumClient, ModuleManager

from examples.deploy import RUST_RUNTIME_ID, SUPERVISOR_ARTIFACT_NAME, SUPERVISOR_ARTIFACT_VERSION


def run() -> None:
    """Example of downloading the Protobuf sources and using the compiled
    module."""
    client = ExonumClient(hostname="127.0.0.1", public_api_port=8080, private_api_port=8081)

    # Create ProtobufLoader via context manager (so that we will not have to
    # initialize/deinitialize it manually):
    with client.protobuf_loader() as loader:
        # Load core proto files:
        loader.load_main_proto_files()
        # Load proto files for the Exonum supervisor service:
        loader.load_service_proto_files(RUST_RUNTIME_ID, SUPERVISOR_ARTIFACT_NAME, SUPERVISOR_ARTIFACT_VERSION)

        # Load the main module (runtime.proto):
        runtime_base_module = ModuleManager.import_main_module("exonum.runtime.base")

        # Create a Protobuf message object:
        artifact_id = runtime_base_module.ArtifactId()
        artifact_id.runtime_id = RUST_RUNTIME_ID
        artifact_id.name = "some_service:0.1.0"

        # Working with Protobuf objects, you have to follow Protobuf Python API
        # conventions. See Protobuf Python API docs for details:
        instance_spec = runtime_base_module.InstanceSpec()
        instance_spec.artifact.CopyFrom(artifact_id)

        # Load the service module (service.proto from the supervisor service):
        service_module = ModuleManager.import_service_module(
            SUPERVISOR_ARTIFACT_NAME, SUPERVISOR_ARTIFACT_VERSION, "service"
        )

        # Workflow is the same as for the main modules:
        _deploy_request = service_module.DeployRequest()


if __name__ == "__main__":
    run()
