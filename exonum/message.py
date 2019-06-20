import json
import codecs
from struct import pack, unpack

from pysodium import crypto_sign_keypair, crypto_hash_sha256, crypto_sign_detached
from importlib import import_module

MINIMUM_TX_BODY_LENGTH_HEX = 204  # It calculated as first 76 metadata bytes plus signature with 128 bytes length
PUBLIC_KEY_LENGTH_HEX = 64
SIGNATURE_LENGTH_HEX = 128
SERVICE_ID_START_POSITION_TX = 68
MESSAGE_ID_START_POSITION_TX = 72
PROTO_MESSAGE_START_POSITION_TX = 76
U16_LENGTH_HEX = 4


class MessageGenerator(object):
    def __init__(self, pb_module, service_id):
        self.service_id = service_id
        self.message_ids = dict()
        self.module = pb_module
        for i, message in enumerate(pb_module.DESCRIPTOR.message_types_by_name):
            self.message_ids[message] = i

    def create_message(self, tx_name, **kwargs):
        cls = getattr(import_module(self.module.__name__), tx_name)
        msg = cls()
        for field, value in kwargs.items():
            setattr(msg, field, value)

        return ExonumMessage(self.service_id, self.message_ids[tx_name], msg)


class ExonumMessage(object):
    def __init__(self, service_id, message_id, msg):
        self.author = None
        self.service_id = service_id
        self.message_id = message_id
        self.data = msg
        self.payload = None
        self.signature = None
        self.raw = bytearray()

    def sign(self, keys):
        pk, sk = keys
        self.author = pk

        self.payload = self.data.SerializeToString()

        self.raw.extend(pk)
        self.raw.extend(pack("<B", 0))  # 0 and 0 it's tag and class of TX message
        self.raw.extend(pack("<B", 0))
        self.raw.extend(pack("<H", self.service_id))
        self.raw.extend(pack("<H", self.message_id))
        self.raw.extend(self.payload)
        self.raw.extend(
            crypto_sign_detached(bytes(self.raw), sk)
        )  # calculating signature

        return self

    def to_json(self):
        return json.dumps({"tx_body": encode(self.raw)}, indent=4)

    def hash(self):
        tx_hash = crypto_hash_sha256(bytes(self.raw))
        return encode(tx_hash)

    def get_author(self):
        return self.author

    @classmethod
    def from_hex(cls, tx_hex, proto_class, min_length=MINIMUM_TX_BODY_LENGTH_HEX):
        if len(tx_hex) < min_length:
            return None
        try:
            author = bytes.fromhex(tx_hex[:PUBLIC_KEY_LENGTH_HEX])
            service_id = unpack("<H", codecs.decode(tx_hex[SERVICE_ID_START_POSITION_TX:
                                                           SERVICE_ID_START_POSITION_TX +
                                                           U16_LENGTH_HEX], "hex"))[0]
            message_id = unpack("<H", codecs.decode(tx_hex[MESSAGE_ID_START_POSITION_TX:
                                                           MESSAGE_ID_START_POSITION_TX +
                                                           U16_LENGTH_HEX], "hex"))[0]
            signature = bytes.fromhex(tx_hex[-SIGNATURE_LENGTH_HEX:])
            payload = bytes.fromhex(tx_hex[PROTO_MESSAGE_START_POSITION_TX:
                                           -SIGNATURE_LENGTH_HEX])
        except (ValueError, IndexError):
            return None

        message = proto_class()
        # Possible throws exception
        message.ParseFromString(payload)

        exonum_message = ExonumMessage(service_id, message_id, message)
        exonum_message.signature = signature
        exonum_message.author = author
        exonum_message.payload = payload
        return exonum_message


def gen_keypair():
    return crypto_sign_keypair()


def encode(bytes):
    return codecs.encode(bytes, "hex").decode("utf-8")


def hash(data):
    return crypto_hash_sha256(data)
