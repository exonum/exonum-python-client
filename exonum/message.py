import json
import codecs
from struct import pack
from protobuf3.message import Message
from pysodium import crypto_sign_keypair, crypto_hash_sha256, crypto_sign_detached


class ExonumMessage(object):
    def __init__(self, service_id, message_id, msg):
        self.author_ = None
        self.service_id = service_id
        self.message_id = message_id
        self.payload = (
            msg.encode_to_bytes()
            if isinstance(msg, Message)
            else msg.SerializeToString()
        )
        self.raw = bytearray()

    def sign(self, keys):
        pk, sk = keys
        self.author_ = pk

        self.raw.extend(pk)
        self.raw.extend(pack("<B", 0))  # 0 and 0 it's tag and class of TX message
        self.raw.extend(pack("<B", 0))
        self.raw.extend(pack("<H", self.service_id))
        self.raw.extend(pack("<H", self.message_id))
        self.raw.extend(self.payload)
        self.raw.extend(
            crypto_sign_detached(bytes(self.raw), sk)
        )  # calculating signature

    def to_json(self):
        return json.dumps({"tx_body": encode(self.raw)}, indent=4)

    def hash(self):
        tx_hash = crypto_hash_sha256(bytes(self.raw))
        return encode(tx_hash)

    def author(self):
        return self.author_


def gen_keypair():
    return crypto_sign_keypair()


def encode(bytes):
    return codecs.encode(bytes, "hex").decode("utf-8")
