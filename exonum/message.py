import json
import codecs
from struct import pack, unpack

from pysodium import crypto_sign_keypair, crypto_hash_sha256, crypto_sign_detached, crypto_sign_verify_detached
from google.protobuf.message import DecodeError as ProtobufDecodeError

from .module_manager import ModuleManager

MINIMUM_TX_BODY_LENGTH_HEX = 204  # It calculated as first 76 metadata bytes plus signature with 128 bytes length
PUBLIC_KEY_LENGTH_HEX = 64
SIGNATURE_LENGTH_HEX = 128
SIGNATURE_LENGTH_BYTES = SIGNATURE_LENGTH_HEX // 2
SERVICE_ID_START_POSITION_TX = 68
MESSAGE_ID_START_POSITION_TX = 72
PROTO_MESSAGE_START_POSITION_TX = 76
U16_LENGTH_HEX = 4


class MessageGenerator:
    def __init__(self, service_id, service_name):
        self.service_id = service_id

        self.service_name = service_name
        self.message_ids = dict()

        self.service_module = ModuleManager.import_service_module(service_name, "service")
        for i, message in enumerate(self.service_module.DESCRIPTOR.message_types_by_name):
            self.message_ids[message] = i

    def create_message(self, tx_name, msg):
        return ExonumMessage(self.service_id, self.message_ids[tx_name], msg)


class ExonumMessage:
    def __init__(self, service_id, message_id, msg):
        self.author = None
        self.service_id = service_id
        self.message_id = message_id
        self.msg = msg
        self.payload = None
        self.signature = None
        self.raw = bytearray()

        self._build_message()

    def _build_message(self):
        runtime_mod = ModuleManager.import_main_module("runtime")
        consensus_mod = ModuleManager.import_main_module("consensus")

        serialized_msg = self.msg.SerializeToString()

        call_info = runtime_mod.CallInfo()
        call_info.instance_id = self.service_id
        call_info.method_id = self.message_id

        any_tx = runtime_mod.AnyTx()
        any_tx.call_info.CopyFrom(call_info)
        any_tx.arguments = serialized_msg

        exonum_message = consensus_mod.ExonumMessage()
        exonum_message.any_tx.CopyFrom(any_tx)

        self.payload = exonum_message.SerializeToString()

    def sign(self, keys):
        pk, sk = keys
        self.author = pk

        consensus_mod = ModuleManager.import_main_module("consensus")
        helpers_mod = ModuleManager.import_main_module("helpers")

        signed_message = consensus_mod.SignedMessage()
        signed_message.payload = self.payload
        signed_message.author.CopyFrom(helpers_mod.PublicKey(data=pk))

        signature = bytes(crypto_sign_detached(signed_message.payload, sk))

        signed_message.signature.CopyFrom(helpers_mod.Signature(data=signature))

        self.signature = signature

        self.raw = bytes(signed_message.SerializeToString())
        return self

    def to_json(self):
        return json.dumps({"tx_body": encode(self.raw)}, indent=4)

    def hash(self):
        tx_hash = crypto_hash_sha256(bytes(self.raw))
        return encode(tx_hash)

    def get_author(self):
        return self.author

    def validate(self):
        """
        Validates message
        Checks tx signature is correct
        :return: bool
        """
        try:
            consensus_mod = ModuleManager.import_main_module("consensus")

            signed_msg = consensus_mod.SignedMessage()
            signed_msg.ParseFromString(self.raw)

            crypto_sign_verify_detached(self.signature, signed_msg.payload, self.author)
        except (ProtobufDecodeError, ValueError):
            return False
        return True

    @staticmethod
    def from_hex(tx_hex, service_name, tx_name):
        try:
            consensus_mod = ModuleManager.import_main_module("consensus")
            runtime_mod = ModuleManager.import_main_module("runtime")
            service_mod = ModuleManager.import_service_module(service_name, "service")
            transaction_class = getattr(service_mod, tx_name)

            tx_raw = bytes.fromhex(tx_hex)

            signed_msg = consensus_mod.SignedMessage()
            signed_msg.ParseFromString(tx_raw)

            exonum_msg = consensus_mod.ExonumMessage()
            exonum_msg.ParseFromString(signed_msg.payload)

            any_tx = exonum_msg.any_tx

            decoded_msg = transaction_class()
            decoded_msg.ParseFromString(any_tx.arguments)

            # TODO check correctness of the data getting
            service_id = any_tx.call_info.instance_id
            message_id = any_tx.call_info.method_id
            signature = signed_msg.signature.data[:]
            author = signed_msg.author.data[:]

            exonum_message = ExonumMessage(service_id, message_id, decoded_msg)
            exonum_message.signature = signature
            exonum_message.author = author
            exonum_message.payload = signed_msg.payload
            exonum_message.raw = tx_raw
            return exonum_message
        except ProtobufDecodeError:
            return None


def gen_keypair():
    return crypto_sign_keypair()


def encode(bytes):
    return codecs.encode(bytes, "hex").decode("utf-8")


def hash(data):
    return crypto_hash_sha256(data)
