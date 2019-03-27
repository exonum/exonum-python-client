import proto.cryptocurrency_pb2
from exonum.client import ExonumClient
from exonum.message import MessageGenerator, gen_keypair, encode


def event_handler(data):
    print(data)


def main():
    try:
        # Creation client, subscriber and message generator
        client = ExonumClient("cryptocurrency", "192.168.1.177", 9081)
        subscriber = client.create_subscriber()
        msg_generator = MessageGenerator(proto.cryptocurrency_pb2, 128)

        # Creation Alice's wallet
        alice_keys = gen_keypair()
        alice_msg = msg_generator.create_message("CreateWallet", name="Alice")
        client.send_transaction(alice_msg.sign(alice_keys))
        subscriber.wait_for_new_block()
        print(client.get_tx_info(alice_msg.hash()))

        # Creation Bob's wallet
        bob_keys = gen_keypair()
        bob_msg = msg_generator.create_message("CreateWallet", name="Bob")
        client.send_transaction(bob_msg.sign(alice_keys))
        subscriber.wait_for_new_block()
        print(client.get_tx_info(bob_msg.hash()))

        # Transfer funds from Bob's wallet to Alice's
        transfer_msg = msg_generator.create_message("Transfer", amount=10, seed=12345)
        transfer_msg.data.to.data = alice_keys[0]
        print(client.send_transaction(transfer_msg.sign(bob_keys)))
        subscriber.wait_for_new_block()
        print(client.get_tx_info(transfer_msg.hash()))

        print(client.get_service("wallets/info?pub_key=" + encode(alice_keys[0])))
        print(client.health_info())
        print(client.mempool())
        print(client.user_agent())

        subscriber.stop()

        print("Bye, demo is over...")
    except KeyboardInterrupt:
        subscriber.stop()


if __name__ == "__main__":
    main()
