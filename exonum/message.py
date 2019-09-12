"""This module is capable of creating and signing of the Exonum transactions."""

from typing import Tuple, Dict, Optional
import json

from pysodium import crypto_sign_keypair, crypto_hash_sha256, crypto_sign_detached, crypto_sign_verify_detached
from google.protobuf.message import Message as ProtobufMessage, DecodeError as ProtobufDecodeError

from .module_manager import ModuleManager


class MessageGenerator:
    def __init__(self, service_id: int, service_name: str):
        self.service_id = service_id

        self.service_name = service_name
        self.message_ids: Dict[str, int] = dict()

        self.service_module = ModuleManager.import_service_module(service_name, "service")
        for i, message in enumerate(self.service_module.DESCRIPTOR.message_types_by_name):
            self.message_ids[message] = i

    def create_message(self, tx_name: str, message: ProtobufMessage) -> "ExonumMessage":
        return ExonumMessage(self.service_id, self.message_ids[tx_name], message)


class ExonumMessage:
    def __init__(self, service_id: int, message_id: int, msg: ProtobufMessage):
        self.author: Optional[bytes] = None
        self.service_id = service_id
        self.message_id = message_id
        self.msg = msg
        self.payload: Optional[bytes] = None
        self.signature: Optional[bytes] = None
        self.raw = bytes()

        self._build_message()

    def _build_message(self) -> None:
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

    def sign(self, keys: Tuple[bytes, bytes]) -> "ExonumMessage":
        public_key, secret_key = keys
        self.author = public_key

        consensus_mod = ModuleManager.import_main_module("consensus")
        helpers_mod = ModuleManager.import_main_module("helpers")

        signed_message = consensus_mod.SignedMessage()
        signed_message.payload = self.payload
        signed_message.author.CopyFrom(helpers_mod.PublicKey(data=public_key))

        signature = bytes(crypto_sign_detached(signed_message.payload, secret_key))

        signed_message.signature.CopyFrom(helpers_mod.Signature(data=signature))

        self.signature = signature

        self.raw = bytes(signed_message.SerializeToString())
        return self

    def to_json(self) -> str:
        return json.dumps({"tx_body": self.raw.hex()}, indent=4)

    def hash(self) -> str:
        tx_hash = _hash(self.raw)
        return tx_hash.hex()

    def get_author(self) -> Optional[bytes]:
        return self.author

    def validate(self) -> bool:
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
    def from_hex(tx_hex: str, service_name: str, tx_name: str) -> Optional["ExonumMessage"]:
        try:
            consensus_mod = ModuleManager.import_main_module("consensus")
            service_mod = ModuleManager.import_service_module(service_name, "service")
            transaction_class = getattr(service_mod, tx_name)

            tx_raw = bytes(bytes.fromhex(tx_hex))

            signed_msg = consensus_mod.SignedMessage()
            signed_msg.ParseFromString(tx_raw)

            exonum_msg = consensus_mod.ExonumMessage()
            exonum_msg.ParseFromString(signed_msg.payload)

            any_tx = exonum_msg.any_tx

            decoded_msg = transaction_class()
            decoded_msg.ParseFromString(any_tx.arguments)

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


def gen_keypair() -> Tuple[bytes, bytes]:
    return crypto_sign_keypair()


def _hash(data: bytes) -> bytes:
    return crypto_hash_sha256(data)
