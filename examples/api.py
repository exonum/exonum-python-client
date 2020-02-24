"""Example of a Basic API Interaction via Exonum Python Light Client."""
from exonum_client import ExonumClient


def run() -> None:
    """Example of a simple API interaction."""
    client = ExonumClient(hostname="127.0.0.1", public_api_port=8080, private_api_port=8081)

    # Get the available services:
    print("Available services:")
    available_services_response = client.public_api.available_services()
    if available_services_response.status_code == 200:
        available_services = available_services_response.json()
        print(" Artifacts:")
        for artifact in available_services["artifacts"]:
            print(f"  - {artifact['name']}:{artifact['version']} (runtime ID {artifact['runtime_id']})")
        print(" Instances:")
        for state in available_services["services"]:
            instance = state["spec"]
            print(f"  - ID {instance['id']} => {instance['name']} (artifact {instance['artifact']['name']})")
    else:
        print("Available services request failed")
    print("")

    # Get the health info:
    print("Node info:")
    node_info_response = client.private_api.get_info()
    if node_info_response.status_code == 200:
        node_info = node_info_response.json()
        print(f"Consensus status: {node_info['consensus_status']}")
        print(f"Connected peers: {node_info['connected_peers']}")
    else:
        print("Node info request failed.")
    print("")

    # Get the Exonum stats:
    print("Exonum stats:")
    stats_response = client.private_api.get_stats()
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"Current height: {stats['height']}")
        print(f"Tx pool size: {stats['tx_pool_size']}")
        print(f"Tx count: {stats['tx_count']}")
        print(f"Tx cache size: {stats['tx_cache_size']}")
    else:
        print("Stats request failed.")
    print("")


if __name__ == "__main__":
    run()
