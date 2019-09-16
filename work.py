def event_handler(data):
    print(data)


def example_run():
    # Example of usage.

    from exonum import ExonumClient, ModuleManager, MessageGenerator, gen_keypair
    import codecs
    import json
    import time
    import requests

    client = ExonumClient(hostname="127.0.0.1", public_api_port=8080, private_api_port=8081)

    with client.protobuf_loader() as loader:
        loader.load_main_proto_files()
        loader.load_service_proto_files(0, "exonum-supervisor:0.12.0")

        service_module = ModuleManager.import_service_module("exonum-supervisor:0.12.0", "service")

        print(client.available_services().json())

        # Create subscriber
        # TODO FIXME subscriber is not created for some reason (Handshake Status 400)

        # Deploy cryptocurrency service

        cryptocurrency_service_name = "exonum-cryptocurrency-advanced:0.12.0"
        deploy_request = service_module.DeployRequest()
        deploy_request.artifact.runtime_id = 0
        deploy_request.artifact.name = cryptocurrency_service_name
        deploy_request.deadline_height = 1000000

        hex_request = codecs.encode(deploy_request.SerializeToString(), "hex").decode("utf-8")

        request_json = json.dumps(hex_request)
        supervisor_endpoint = "http://127.0.0.1:8081/api/services/supervisor/{}"
        deploy_endpoint = supervisor_endpoint.format("deploy-artifact")

        print(client.service_endpoint("supervisor", "deploy-artifact", private=True))

        response = requests.post(deploy_endpoint, request_json, headers={"content-type": "application/json"})

        print("-------")
        print(response.json())

        # Wait for new blocks

        with client.create_subscriber() as subscriber:
            subscriber.wait_for_new_block()
            subscriber.wait_for_new_block()

        # Start cryptocurrency service

        start_request = service_module.StartService()
        start_request.artifact.runtime_id = 0
        start_request.artifact.name = cryptocurrency_service_name
        start_request.name = "XNM"
        start_request.deadline_height = 1000000

        hex_request = codecs.encode(start_request.SerializeToString(), "hex").decode("utf-8")

        request_json = json.dumps(hex_request)
        start_endpoint = supervisor_endpoint.format("start-service")

        response = requests.post(start_endpoint, request_json, headers={"content-type": "application/json"})

        # Sleep a bit until exonum will restart the server

        time.sleep(1)

        # Wait for new blocks

        with client.create_subscriber() as subscriber:
            subscriber.wait_for_new_block()
            subscriber.wait_for_new_block()

        print("-----")
        print(client.available_services().json())

        # Work with cryptocurrency

        keys_1 = gen_keypair()
        keys_2 = gen_keypair()

        loader.load_service_proto_files(0, cryptocurrency_service_name)

        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, "service")

        cryptocurrency_message_generator = MessageGenerator(1024, cryptocurrency_service_name)

        # Create wallet for Alice

        create_wallet_alice = cryptocurrency_module.CreateWallet()
        create_wallet_alice.name = "Alice1"
        create_wallet_alice_tx = cryptocurrency_message_generator.create_message(create_wallet_alice)
        create_wallet_alice_tx.sign(keys_1)

        # Create wallet for Bob

        create_wallet_bob = cryptocurrency_module.CreateWallet()
        create_wallet_bob.name = "Bob2"
        create_wallet_bob_tx = cryptocurrency_message_generator.create_message(create_wallet_bob)
        create_wallet_bob_tx.sign(keys_2)

        responses = client.send_transactions([create_wallet_alice_tx, create_wallet_bob_tx])

        # Wait for new blocks

        with client.create_subscriber() as subscriber:
            subscriber.wait_for_new_block()
            subscriber.wait_for_new_block()

        # Show transactions statuses

        for response in responses:
            print("RESPONSE")
            print(response.json())
            res = client.get_tx_info(response.json()["tx_hash"])
            print(res.json())

            block_height = res.json()["location"]["block_height"]

            block_info = client.get_block(block_height).json()

            print("Block info: \n{}\n-----\n".format(block_info))

        # Some additional info.
        print(client.health_info().json())
        print(client.mempool())
        print(client.user_agent().json())

        subscriber.stop()


def main():
    example_run()


if __name__ == "__main__":
    main()
