from time import sleep
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


client = ExonumClient("cryptocurrency", "localhost", 9081)

alice_message = create_wallet_msg("Alice")
bob_message = create_wallet_msg("Bob")

alice_keys = gen_keypair()
alice_tx = ExonumMessage(128, 2, alice_message.encode_to_bytes())
alice_tx.sign(alice_keys)

bob_keys = gen_keypair()
bob_tx = ExonumMessage(128, 2, bob_message.encode_to_bytes())
bob_tx.sign(bob_keys)

client.send_transaction(alice_tx)
client.send_transaction(bob_tx)
sleep(2)

print(client.get_tx_info(alice_tx.hash()))
print(client.get_tx_info(bob_tx.hash()))

transfer_msg = Transfer()
transfer_msg.to.data = alice_tx.author()
transfer_msg.amount = 10
transfer_msg.seed = 0
transfer_tx = ExonumMessage(128, 0, transfer_msg.encode_to_bytes())
transfer_tx.sign(bob_keys)
client.send_transaction(transfer_tx)
sleep(2)
print(client.get_tx_info(transfer_tx.hash()))

print(client.get_service("wallets/info?pub_key=" + encode(alice_keys[0])))

print(client.health_info())
print(client.mempool())
print(client.user_agent())
