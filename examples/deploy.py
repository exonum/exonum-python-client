"""Example script for deploying cryptocurrency-advanced service."""
import time
import json
from exonum import ExonumClient, ModuleManager

RUST_RUNTIME_ID = 0


def run() -> None:
    """Example script for deploying cryptocurrency-advanced service.
    This script is intended only to demonstate client possibilites,
    for actual deployment consider using `exonum-launcher` tool."""
    client = ExonumClient(hostname="127.0.0.1", public_api_port=8080, private_api_port=8081)

    # Name of the artifact.
    service_name = "exonum-cryptocurrency-advanced:0.12.0"

    # Name of the service instance we want to create.
    instance_name = "XNM"

    with client.protobuf_loader() as loader:
        # Load and compile proto files.
        loader.load_main_proto_files()
        loader.load_service_proto_files(RUST_RUNTIME_ID, "exonum-supervisor:0.12.0")

        try:
            print(f"Started deploying `{service_name}` artifact.")
            deploy_service(client, service_name)

            print(f"Artifact `{service_name}` successfully deployed.")

            print(f"Started enablind `{instance_name}` instance.")

            instance_id = start_service(client, service_name, instance_name)

            # If no exception occured during the previous calls, everything is OK.
            print(f"Service instance '{instance_name}' (artifact '{service_name}') started with ID {instance_id}.")
        except RuntimeError as err:
            print(f"Service instance '{instance_name}' (artifact '{service_name}') deployment failed with error {err}")


def deploy_service(client: ExonumClient, service_name: str) -> None:
    """This functions sends a deploy request for the desired service service
    and waits until it's deployed."""

    # Create deploy request message.
    service_module = ModuleManager.import_service_module("exonum-supervisor:0.12.0", "service")

    deploy_request = service_module.DeployRequest()
    deploy_request.artifact.runtime_id = 0  # Rust runtime ID.
    deploy_request.artifact.name = service_name
    deploy_request.deadline_height = 1000000  # Some big number (we won't have to wait that long, it's just a deadline).

    # Convert request from Protobuf message to bytes.
    request_bytes = deploy_request.SerializeToString()

    # Send request and wait for Exonum to process it.
    send_request(client, "deploy-artifact", request_bytes)

    # Ensure that service is added to the available modules.
    available_services = client.available_services().json()
    if service_name not in map(lambda x: x["name"], available_services["artifacts"]):
        raise RuntimeError(f"{service_name} is not listed in available services after deployment")

    # Everything is OK, service is deployed.


def start_service(client: ExonumClient, service_name: str, instance_name: str) -> int:
    """This function starts the previously deployed service instance."""

    # Create start request.
    service_module = ModuleManager.import_service_module("exonum-supervisor:0.12.0", "service")
    start_request = service_module.StartService()
    start_request.artifact.runtime_id = 0  # Rust runtime ID.
    start_request.artifact.name = service_name
    start_request.name = instance_name
    start_request.deadline_height = 1000000  # Some big number.

    # Convert request from Protobuf message to bytes.
    request_bytes = start_request.SerializeToString()

    # Send request and wait for Exonum to process it.
    send_request(client, "start-service", request_bytes)

    # Ensure that service is added to the running instances list.
    available_services = client.available_services().json()
    if instance_name not in map(lambda x: x["name"], available_services["services"]):
        raise RuntimeError(f"{instance_name} is not listed in running instances after starting")

    # Everything is OK, service is started.
    # Return the running instance ID.
    for instance in available_services["services"]:
        if instance["name"] == instance_name:
            return instance["id"]

    raise RuntimeError("Instance ID was not found")


def send_request(client: ExonumClient, endpoint: str, data: bytes) -> None:
    """This function encodes request from bytes to JSON, sends it to the Exonum and waits."""
    # Convert request to the hexadecimal string.
    hex_request = data.hex()

    # Convert request to json.
    json_request = json.dumps(hex_request)

    # Post request to the exonum.
    response = client.post_service("supervisor", endpoint, json_request, private=True)

    if response.status_code != 200:
        error_msg = f"Error occured during the request to the '{endpoint}' endpoint: {response.content}"
        raise RuntimeError(error_msg)

    # Wait for 10 seconds
    # TODO currently due to the bug in the exonum it takes up to 10 seconds to update dispatcher info.
    time.sleep(10)


if __name__ == "__main__":
    run()
