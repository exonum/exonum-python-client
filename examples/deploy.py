"""Example Script for Deploying the Cryptocurrency Advanced Service."""
import time
import json
from exonum_client import ExonumClient, ModuleManager

RUST_RUNTIME_ID = 0
SUPERVISOR_ARTIFACT_NAME = "exonum-supervisor:0.13.0-rc.2"
CRYPTOCURRENCY_ARTIFACT_NAME = "exonum-cryptocurrency-advanced:0.13.0-rc.2"
CRYPTOCURRENCY_INSTANCE_NAME = "XNM"


def run() -> None:
    """This is an example script for deploying the Cryptocurrency Advanced
    service.
    This script is intended only to demonstrate client possibilities.
    For actual deployment consider using `exonum-launcher` tool."""
    client = ExonumClient(hostname="127.0.0.1", public_api_port=8080, private_api_port=8081)

    # Create better-looking aliases for constants.
    service_name = CRYPTOCURRENCY_ARTIFACT_NAME
    instance_name = CRYPTOCURRENCY_INSTANCE_NAME

    with client.protobuf_loader() as loader:
        # Load and compile proto files:
        loader.load_main_proto_files()
        loader.load_service_proto_files(RUST_RUNTIME_ID, SUPERVISOR_ARTIFACT_NAME)

        try:
            print(f"Started deploying `{service_name}` artifact.")
            deploy_service(client, service_name)

            print(f"Artifact `{service_name}` successfully deployed.")

            print(f"Started enablind `{instance_name}` instance.")

            instance_id = start_service(client, service_name, instance_name)

            # If no exception has occured during the previous calls, the service
            # has started successfully:
            print(f"Service instance '{instance_name}' (artifact '{service_name}') started with ID {instance_id}.")
        except RuntimeError as err:
            print(f"Service instance '{instance_name}' (artifact '{service_name}') deployment failed with error {err}")


def deploy_service(client: ExonumClient, service_name: str) -> None:
    """This function sends a deploy request for the desired service
    and waits until it is deployed."""

    # Create a deploy request message:
    service_module = ModuleManager.import_service_module(SUPERVISOR_ARTIFACT_NAME, "service")

    deploy_request = service_module.DeployRequest()
    deploy_request.artifact.runtime_id = 0  # Rust runtime ID.
    deploy_request.artifact.name = service_name
    deploy_request.deadline_height = 1000000  # Some big number (we won't have to wait that long, it's just a deadline).

    # Convert the request from a Protobuf message to bytes:
    request_bytes = deploy_request.SerializeToString()

    # Send the request and wait for Exonum to process it:
    send_request(client, "deploy-artifact", request_bytes)

    # Ensure that the service is added to the available modules:
    available_services = client.available_services().json()
    if service_name not in map(lambda x: x["name"], available_services["artifacts"]):
        raise RuntimeError(f"{service_name} is not listed in available services after deployment")

    # Service is deployed.


def start_service(client: ExonumClient, service_name: str, instance_name: str) -> int:
    """This function starts the previously deployed service instance."""

    # Create a start request:
    service_module = ModuleManager.import_service_module(SUPERVISOR_ARTIFACT_NAME, "service")
    start_request = service_module.StartService()
    start_request.artifact.runtime_id = 0  # Rust runtime ID.
    start_request.artifact.name = service_name
    start_request.name = instance_name

    # Create a config change object:
    config_change = service_module.ConfigChange()
    config_change.start_service.CopyFrom(start_request)

    # Create a config proposal:
    config_proposal = service_module.ConfigPropose()
    config_proposal.changes.append(config_change)

    # Convert the config proposal from a Protobuf message to bytes:
    request_bytes = config_proposal.SerializeToString()

    # Send the request and wait for Exonum to process it:
    send_request(client, "propose-config", request_bytes)

    # Ensure that the service is added to the running instances list:
    available_services = client.available_services().json()
    if instance_name not in map(lambda x: x["spec"]["name"], available_services["services"]):
        raise RuntimeError(f"{instance_name} is not listed in running instances after starting")

    # Service has started.
    # Return the running instance ID:
    for state in available_services["services"]:
        instance = state["spec"]
        if instance["name"] == instance_name:
            return instance["id"]

    raise RuntimeError("Instance ID was not found")


def send_request(client: ExonumClient, endpoint: str, data: bytes) -> None:
    """This function encodes request from bytes to JSON, sends it to the Exonum and waits."""
    # Convert the request to a hexadecimal string:
    hex_request = data.hex()

    # Convert the request to a JSON:
    json_request = json.dumps(hex_request)

    # Post the request to Exonum:
    response = client.post_service("supervisor", endpoint, json_request, private=True)

    if response.status_code != 200:
        error_msg = f"Error occured during the request to the '{endpoint}' endpoint: {response.content}"
        raise RuntimeError(error_msg)

    # Wait for 10 seconds.
    # TODO: currently due to a bug in Exonum it takes up to 10 seconds to update the dispatcher info:
    time.sleep(10)


if __name__ == "__main__":
    run()
