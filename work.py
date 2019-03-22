import json
from exonum.client import ExonumClient
from exonum.message import ExonumMessage, gen_keypair, encode
from protobuf3.message import Message
from protobuf3.fields import StringField, BytesField, UInt64Field, MessageField


class CreateWallet(Message):
    name = StringField(field_number=1, required=True)


class Transfer(Message):
    class PublicKey(Message):
        data = BytesField(field_number=1, required=True)

    to = MessageField(field_number=1, required=True, message_cls=PublicKey)
    amount = UInt64Field(field_number=2, required=True)
    seed = UInt64Field(field_number=3, required=True)


def create_wallet_msg(name):
    msg = CreateWallet()
    msg.name = name
    return msg


def event_handler(data):
    print(data)
    h = json.loads(data)["height"]
    print("block at height: {} was committing".format(h))


def create_wallet_from_proto(name):
    from proto.cryptocurrency_pb2 import CreateWallet

    msg = CreateWallet()
    msg.name = name
    return msg


def main():
    try:
        client = ExonumClient("cryptocurrency", "192.168.1.177", 9081)
        subscriber = client.create_subscriber()

        alice_message = create_wallet_msg("Alice")
        bob_message = create_wallet_from_proto("Bob")

        alice_keys = gen_keypair()
        alice_tx = ExonumMessage(128, 2, alice_message)
        alice_tx.sign(alice_keys)

        bob_keys = gen_keypair()
        bob_tx = ExonumMessage(128, 2, bob_message)
        bob_tx.sign(bob_keys)

        client.send_transactions([alice_tx, bob_tx])

        subscriber.wait_for_event()

        print(client.get_tx_info(alice_tx.hash()))
        print(client.get_tx_info(bob_tx.hash()))

        subscriber.set_handler(event_handler)
        subscriber.run()

        transfer_msg = Transfer()
        transfer_msg.to.data = alice_tx.author()
        transfer_msg.amount = 10
        transfer_msg.seed = 0
        transfer_tx = ExonumMessage(128, 0, transfer_msg)
        transfer_tx.sign(bob_keys)

        client.send_transaction(transfer_tx)

        subscriber.wait_for_event()

        print(client.get_tx_info(transfer_tx.hash()))

        print(client.get_service("wallets/info?pub_key=" + encode(alice_keys[0])))

        print(client.health_info())
        print(client.mempool())
        print(transfer_tx.hash())
        print(client.user_agent())
        subscriber.stop()
        print("Bye, demo is over...")
    except KeyboardInterrupt:
        subscriber.stop()


if __name__ == "__main__":
    main()
