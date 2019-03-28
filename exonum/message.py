import json
import codecs
from struct import pack
from protobuf3.message import Message
from pysodium import crypto_sign_keypair, crypto_hash_sha256, crypto_sign_detached
from importlib import import_module


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
        self.raw = bytearray()

    def sign(self, keys):
        pk, sk = keys
        self.author = pk

        self.payload = (
            self.data.encode_to_bytes()
            if isinstance(self.data, Message)
            else self.data.SerializeToString()
        )

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


def gen_keypair():
    return crypto_sign_keypair()


def encode(bytes):
    return codecs.encode(bytes, "hex").decode("utf-8")
