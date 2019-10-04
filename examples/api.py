"""Example of a Basic API Interaction via Exonum Python Light Client."""
from exonum_client import ExonumClient


def run() -> None:
    """Example of a simple API interaction."""
    client = ExonumClient(hostname="127.0.0.1", public_api_port=8080, private_api_port=8081)

    # Get the available services:
    print("Available services:")
    available_services_response = client.available_services()
    if available_services_response.status_code == 200:
        available_services = available_services_response.json()
        print(" Artifacts:")
        for artifact in available_services["artifacts"]:
            print(f"  - {artifact['name']} (runtime ID {artifact['runtime_id']})")
        print(" Instances:")
        for instance in available_services["services"]:
            print(f"  - ID {instance['id']} => {instance['name']} (artifact {instance['artifact']['name']})")
    else:
        print("Available services request failed")
    print("")

    # Get the health info:
    print("Health info:")
    health_info_response = client.health_info()
    if health_info_response.status_code == 200:
        health_info = health_info_response.json()
        print(f"Consensus status: {health_info['consensus_status']}")
        print(f"Connected peers: {health_info['connected_peers']}")
    else:
        print("Health info request failed.")
    print("")

    # Get the Exonum stats:
    print("Exonum stats:")
    stats_response = client.stats()
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"Tx pool size: {stats['tx_pool_size']}")
        print(f"Tx count: {stats['tx_count']}")
        print(f"Tx cache size: {stats['tx_cache_size']}")
    else:
        print("Stats request failed.")
    print("")

    # Get the user agent:
    print("Exonum user agent:")
    user_agent_response = client.user_agent()
    if user_agent_response.status_code == 200:
        user_agent = user_agent_response.json()
        print(f"User agent: {user_agent}")
    else:
        print("User agent request failed.")


if __name__ == "__main__":
    run()
