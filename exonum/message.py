"""This module is capable of creating and signing of the Exonum transactions."""

from typing import Dict, Optional, Tuple, Any
import json

from google.protobuf.message import Message as ProtobufMessage, DecodeError as ProtobufDecodeError

from .crypto import PublicKey, Hash, Signature, KeyPair
from .module_manager import ModuleManager


class MessageGenerator:
    """MessageGenerator is a class which helps you to create transactions.
    It's capable of transforming a Protobuf Message object into an Exonum transaction
    with required metadata set.

    Example of usage:
    >>> instance_id = ... # Get the ID of the desired service instance.
    >>> artifact_name = ... # Get the name of the artifact (not the instance).
    >>> cryptocurrency_message_generator = MessageGenerator(instance_id, artifact_name) # Create the message generator.
    >>> create_wallet_alice = cryptocurrency_module.CreateWallet() # Create the protobuf message.
    >>> create_wallet_alice.name = "Alice1" # Fill the protobuf message manually.

    Then you can transform the Protobuf Message into Exonum Transaction.

    >>> create_wallet_alice_tx = cryptocurrency_message_generator.create_message(create_wallet_alice)
    >>> create_wallet_alice_tx.sign(keypair) # You should sign the message before sending.
    >>> client.send_transaction(create_wallet_alice_tx)
    """

    def __init__(self, instance_id: int, artifact_name: str):
        """MessageGenerator constructor.

        Parameters
        ----------
        instance_id: int
            ID of the desired Exonum service instance.
        artifact_name: str
            The name of the artifact of the service you want to communicate with.
            The name should be in the format provided by Exonum, like 'exonum-cryptocurrency-advanced:0.12.0'.
        """
        self._instance_id = instance_id

        self._artifact_name = artifact_name
        self._message_ids: Dict[str, int] = dict()

        service_module = ModuleManager.import_service_module(artifact_name, "service")
        for i, message in enumerate(service_module.DESCRIPTOR.message_types_by_name):
            self._message_ids[message] = i

    def create_message(self, message: ProtobufMessage) -> "ExonumMessage":
        """Method to convert Protobuf message into Exonum message.

        Parameters
        ----------
        message: google.protobuf.message.Message
            An protobuf message.

        Returns
        -------
        exonum_message: ExonumMessage
            Exonum message object.
        """

        tx_name = type(message).__name__
        return ExonumMessage(self._instance_id, self._message_ids[tx_name], message)


class ExonumMessage:
    """Generic Exonum transaction class.

    Exonum Message is intended to be created:
     - by using MessageGenerator (if you want to send a transaction to the Exonum blockchain)
     - by using ExonumMessage.from_hex (if you want to parse retrieved transaction).

    Example workflow:

    Sending a message:

    >>> instance_id = ... # Get the ID of the desired service instance.
    >>> artifact_name = ... # Get the name of the artifact (not the instance).
    >>> cryptocurrency_message_generator = MessageGenerator(instance_id, artifact_name) # Create the message generator.
    >>> create_wallet_alice = cryptocurrency_module.CreateWallet() # Create the protobuf message.
    >>> create_wallet_alice.name = "Alice1" # Fill the protobuf message manually.
    >>> create_wallet_alice_tx = cryptocurrency_message_generator.create_message(create_wallet_alice)
    >>> create_wallet_alice_tx.sign(keypair) # You should sign the message before sending.
    >>> client.send_transaction(create_wallet_alice_tx)

    Parsing a message:

    >>> message_hex = ... # Retrieve a message as a hexadecimal string.
    >>> artifact_name = ... # Get the name of the artifact (not the instance).
    >>> transaction_name = "CreateWallet" # Get the name of the transaction.
    >>> parsed_message = ExonumMessage.from_hex(message_hex, artifact_name, transaction_name)
    >>> assert parsed_message.validate() # Verify the signature of the retrieved message.

    Other methods:
    >>> message = ExonumMessage.from_hex(...)
    >>> author = message.author() # Get the author's public key.
    >>> tx_hash = message.hash() # Get the transaction hash.
    >>> signature = message.signature() # Get the transaction signature.
    >>> any_tx_raw = message.any_tx_raw() # Get the message's AnyTx serialized to bytes.
    >>> signed_tx_raw = message.signed_tx_raw() # Get the message's SignedMessage serialized to bytes.
    >>> tx_json = message.pack_into_json() # Create the JSON with the transaction in the format expected by Exonum.
    """

    def __init__(self, instance_id: int, message_id: int, msg: ProtobufMessage, prebuilt: Optional[bytes] = None):
        """Exonum Message constructor. It's not intended to be used directly, see `MessageGenerator.create_message`
        and `ExonumMessage.from_hex` instead."""
        # Author's public key as bytes.
        self._author: Optional[PublicKey] = None
        # ID of the service instance.
        self._instance_id = instance_id
        # ID of the message (to be set in the CallInfo).
        self._message_id = message_id
        # Protobuf message.
        self._msg = msg
        # Signature as bytes.
        self._signature: Optional[Signature] = None
        # AnyTx message serialized to bytes.
        # SignedMessage serialized to bytes.
        self._signed_tx_raw: Optional[bytes] = None

        # If we're parsing the received message, we don't have to build anything.
        if prebuilt is None:
            self._any_tx_raw = self._build_message()
        else:
            self._any_tx_raw = prebuilt

    @classmethod
    def from_hex(cls, message_hex: str, artifact_name: str, tx_name: str) -> Optional["ExonumMessage"]:
        """Attempts to parse Exonum Message from serialized hexadecimal string.

        Parameters
        ----------
        message_hex: str
            Serialized message as a hexadecimal string.
        artifact_name: str
            The name of the artifact of the service you want to communicate with.
            The name should be in the format provided by Exonum, like 'exonum-cryptocurrency-advanced:0.12.0'.
        tx_name: str
            The name of the transaction to be parsed, e.g. 'CreateWallet'.

        Returns
        -------
        parsed_message: Optional[ExonumMessage]
            If parsing was successfull, an ExonumMessage object will be returned.
            Otherwise the return value will be None.
        """
        try:
            signed_msg, exonum_msg, decoded_msg = cls._deserialize_message(message_hex, artifact_name, tx_name)

            service_id = exonum_msg.any_tx.call_info.instance_id
            message_id = exonum_msg.any_tx.call_info.method_id
            signature = signed_msg.signature.data[:]
            author = signed_msg.author.data[:]

            exonum_message = cls(service_id, message_id, decoded_msg, prebuilt=exonum_msg.any_tx.SerializeToString())

            cls._set_signature_data(exonum_message, author, signature, bytes.fromhex(message_hex))
            return exonum_message
        except ProtobufDecodeError:
            return None

    def sign(self, keys: KeyPair) -> None:
        """Signs the message with the provided pair of the keys.

        Please note that signing is required before sending a message to the Exonum blockchain.

        Parameters
        ----------
        keys: exonum.crypto.KeyPair
            A pair of public_key and secret_key as bytes.
        """

        public_key, secret_key = keys.public_key, keys.secret_key
        self._author = public_key

        consensus_mod = ModuleManager.import_main_module("consensus")
        helpers_mod = ModuleManager.import_main_module("helpers")

        signed_message = consensus_mod.SignedMessage()
        signed_message.payload = self._any_tx_raw
        signed_message.author.CopyFrom(helpers_mod.PublicKey(data=public_key.value))

        signature = Signature.sign(signed_message.payload, secret_key)

        signed_message.signature.CopyFrom(helpers_mod.Signature(data=signature.value))

        self._signature = signature

        self._signed_tx_raw = bytes(signed_message.SerializeToString())

    def validate(self) -> bool:
        """
        Validates message
        Checks tx signature is correct
        :return: bool
        """
        if self._signature is None or self._author is None:
            return False

        try:
            consensus_mod = ModuleManager.import_main_module("consensus")

            signed_msg = consensus_mod.SignedMessage()
            signed_msg.ParseFromString(self._signed_tx_raw)

            return self._signature.verify(signed_msg.payload, self._author)
        except (ProtobufDecodeError, ValueError):
            return False

    def pack_into_json(self) -> str:
        """Packs the serialized signed message into the JSON format expected by Exonum.

        Please note that this method does not serialize the message to JSON.

        Returns
        -------
        json_message: str
            String with the JSON representation of serialized message.

        Raises
        ------
        RuntimeError
            An error will be raised on attempt to call `pack_into_json` with the unsigned message.
        """
        if self._signed_tx_raw is None:
            raise RuntimeError("Attempt to call `to_json` on the unsigned message.")
        return json.dumps({"tx_body": self._signed_tx_raw.hex()}, indent=4)

    def hash(self) -> Hash:
        """Returns the hash of the message. If message was not signed, an hash of empty message will be returned."""
        return Hash.hash_data(self._signed_tx_raw)

    # Getters section.

    def author(self) -> Optional[PublicKey]:
        """Returns the author's public key. If author was not set, None will be returned."""
        return self._author

    def signature(self) -> Optional[Signature]:
        """Returns the signature. If message was not signed, None will be returned."""
        return self._signature

    def any_tx_raw(self) -> bytes:
        """Returns the serialized AnyTx message as bytes."""
        return self._any_tx_raw

    def signed_raw(self) -> Optional[bytes]:
        """Returns the serialized SignedMessage as bytes. If message was not signed, None will be returned."""
        return self._signed_tx_raw

    def _set_signature_data(self, author: bytes, signature: bytes, raw: bytes) -> None:
        self._author = PublicKey(author)
        self._signature = Signature(signature)
        self._signed_tx_raw = raw

    def _build_message(self) -> bytes:
        """Builds the raw AnyTx message."""
        runtime_mod = ModuleManager.import_main_module("runtime")
        consensus_mod = ModuleManager.import_main_module("consensus")

        serialized_msg = self._msg.SerializeToString()

        call_info = runtime_mod.CallInfo()
        call_info.instance_id = self._instance_id
        call_info.method_id = self._message_id

        any_tx = runtime_mod.AnyTx()
        any_tx.call_info.CopyFrom(call_info)
        any_tx.arguments = serialized_msg

        exonum_message = consensus_mod.ExonumMessage()
        exonum_message.any_tx.CopyFrom(any_tx)

        return exonum_message.SerializeToString()

    @staticmethod
    def _deserialize_message(message_hex: str, artifact_name: str, tx_name: str) -> Tuple[Any, Any, Any]:
        """Takes a serialized message as an argument and returns a tuple
        [SignedMessage, ExonumMessage,DecodedMessage]."""

        # Load modules and prepare expected message class for parsing.
        consensus_mod = ModuleManager.import_main_module("consensus")
        service_mod = ModuleManager.import_service_module(artifact_name, "service")
        transaction_class = getattr(service_mod, tx_name)

        # Convert message from hex to bytes.
        tx_raw = bytes.fromhex(message_hex)

        # Parse SignedMessage.
        signed_msg = consensus_mod.SignedMessage()
        signed_msg.ParseFromString(tx_raw)

        # Parse ExonumMessage from SignedMessage's payload.
        exonum_msg = consensus_mod.ExonumMessage()
        exonum_msg.ParseFromString(signed_msg.payload)

        # Parse expected message from ExonumMessage's AnyTx arguments.
        decoded_msg = transaction_class()
        decoded_msg.ParseFromString(exonum_msg.any_tx.arguments)

        return signed_msg, exonum_msg, decoded_msg
