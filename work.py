def event_handler(data):
    print(data)

def example_run():
    # Example of usage.

    from .module_manager import ModuleManager
    from .message import MessageGenerator, gen_keypair
    import codecs
    import json
    import time

    with ExonumClient(hostname='127.0.0.1', public_api_port=8080, private_api_port=8081) as client:
        client.load_main_proto_files()
        client.load_service_proto_files(0, 'exonum-supervisor:0.11.0')

        main_module = ModuleManager.import_main_module('consensus')

        service_module = ModuleManager.import_service_module('exonum-supervisor:0.11.0', 'service')
        
        print(client.available_services().json())

        # Create subscriber
        # TODO FIXME subscriber is not created for some reason (Handshake Status 400)

        subscriber = client.create_subscriber()

        # Deploy cryptocurrency service

        cryptocurrency_service_name = 'exonum-cryptocurrency-advanced:0.11.0'
        deploy_request = service_module.DeployRequest()
        deploy_request.artifact.runtime_id = 0
        deploy_request.artifact.name = cryptocurrency_service_name
        deploy_request.deadline_height = 1000000

        hex_request = codecs.encode(deploy_request.SerializeToString(), "hex").decode("utf-8")

        request_json = json.dumps(hex_request)
        supervisor_endpoint = "http://127.0.0.1:8081/api/services/supervisor/{}"
        deploy_endpoint = supervisor_endpoint.format('deploy-artifact')

        response = requests.post(deploy_endpoint, request_json, headers={"content-type": "application/json"})

        print('-------')
        print(response.json())

        # Wait for new blocks
        # TODO Use subscriber

        time.sleep(2)

        # Start cryptocurrency service

        start_request = service_module.StartService()
        start_request.artifact.runtime_id = 0
        start_request.artifact.name = cryptocurrency_service_name
        start_request.name = 'XNM'
        start_request.deadline_height = 1000000

        hex_request = codecs.encode(start_request.SerializeToString(), "hex").decode("utf-8")

        request_json = json.dumps(hex_request)
        start_endpoint = supervisor_endpoint.format('start-service')

        response = requests.post(start_endpoint, request_json, headers={"content-type": "application/json"})

        # Wait for new blocks
        # TODO Use subscriber

        time.sleep(2)

        print('-----')
        print(client.available_services().json())

        # Work with cryptocurrency

        keys = gen_keypair()

        client.load_service_proto_files(0, cryptocurrency_service_name)

        cryptocurrency_module = ModuleManager.import_service_module(cryptocurrency_service_name, 'service')

        cryptocurrency_message_generator = MessageGenerator(1024, cryptocurrency_service_name)

        # Create wallet for Alice

        create_wallet_alice = cryptocurrency_module.CreateWallet()
        create_wallet_alice.name = 'Alice'
        create_wallet_alice_tx = cryptocurrency_message_generator.create_message('CreateWallet', create_wallet_alice)
        create_wallet_alice_tx.sign(keys)

        # Create wallet for Bob

        create_wallet_bob = cryptocurrency_module.CreateWallet()
        create_wallet_bob.name = 'Bob'
        create_wallet_bob_tx = cryptocurrency_message_generator.create_message('CreateWallet', create_wallet_bob)
        create_wallet_bob_tx.sign(keys)

        responses = client.send_transactions([create_wallet_alice_tx, create_wallet_bob_tx])

        # Wait for new blocks
        # TODO Use subscriber

        time.sleep(2)

        # Show transactions statuses

        for response in responses:
            res = client.get_tx_info(response.json()['tx_hash'])
            print(res)
            print(res.json())

        # Some additional info.
        print(client.health_info())
        print(client.mempool())
        print(client.user_agent())

def main():
    example_run()


if __name__ == "__main__":
    main()
