from pysodium import crypto_hash_sha256, crypto_sign_keypair
from tests.proto_test.timestamping_pb2 import TxTimestamp
from tests.proto_test.helpers_pb2 import Hash, PublicKey
from exonum.message import ExonumMessage

HASH_DATA = '1'
SERVICE_ID = 130
MESSAGE_ID = 1


def test_tx_success_parse():
    # Gen init data
    data_hash = crypto_hash_sha256(HASH_DATA.encode())
    keys = crypto_sign_keypair()

    # Prepare original message
    hash_message = Hash()
    hash_message.data = data_hash
    pk_message = PublicKey()
    pk_message.data = keys[0]
    message = TxTimestamp()
    message.content_hash.CopyFrom(hash_message)
    message.owners.extend([pk_message])

    # Create original message
    exonum_message = ExonumMessage(SERVICE_ID, MESSAGE_ID, message)
    exonum_message.sign(keys)

    # Parse message
    parsed_message = ExonumMessage.from_hex(exonum_message.raw.hex(), TxTimestamp)
    assert parsed_message.get_author() == keys[0]
    assert parsed_message.data.content_hash.data == data_hash
    assert parsed_message.service_id == SERVICE_ID
    assert parsed_message.message_id == MESSAGE_ID
    assert parsed_message.data.owners[0].data == keys[0]


def test_tx_fail_parse():
    # Gen init data
    data_hash = crypto_hash_sha256(HASH_DATA.encode())
    keys = crypto_sign_keypair()

    # Prepare original message
    hash_message = Hash()
    hash_message.data = data_hash
    pk_message = PublicKey()
    pk_message.data = keys[0]
    message = TxTimestamp()
    message.content_hash.CopyFrom(hash_message)
    message.owners.extend([pk_message])

    # Create original message
    exonum_message = ExonumMessage(SERVICE_ID, MESSAGE_ID, message)
    exonum_message.sign(keys)

    # Parse message
    corrupted_tx = '1' + exonum_message.raw.hex()
    parsed_message = ExonumMessage.from_hex(corrupted_tx, TxTimestamp)
    assert parsed_message == None
