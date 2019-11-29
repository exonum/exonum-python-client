"""This module is capable of creating and signing Exonum transactions."""

from typing import Dict, Optional, Tuple, Any
import json
from logging import getLogger

from google.protobuf.message import Message as ProtobufMessage, DecodeError as ProtobufDecodeError

from .crypto import PublicKey, Hash, Signature, KeyPair
from .module_manager import ModuleManager

# pylint: disable=C0103
logger = getLogger(__name__)


class MessageGenerator:
    """MessageGenerator is a class which helps you create transactions.
    It is capable of transforming a Protobuf message object into an Exonum transaction
    with a set of the required metadata.

    Example of usage:
    >>> instance_id = ... # Get the ID of the desired service instance.
    >>> artifact_name = ... # Get the name of the artifact (not the instance).
    >>> cryptocurrency_message_generator = MessageGenerator(instance_id, artifact_name) # Create a message generator.
    >>> create_wallet_alice = cryptocurrency_module.CreateWallet() # Create a Protobuf message.
    >>> create_wallet_alice.name = "Alice1" # Fill the Protobuf message manually.

    Then you can transform the Protobuf message into an Exonum transaction.

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
            The name of the service artifact you want to communicate with.
            The name should be in the format provided by Exonum, like 'exonum-cryptocurrency-advanced:0.12.0'.
        """
        self._instance_id = instance_id

        self._artifact_name = artifact_name
        self._message_ids: Dict[str, int] = dict()

        service_module = ModuleManager.import_service_module(artifact_name, "service")
        for i, message in enumerate(service_module.DESCRIPTOR.message_types_by_name):
            self._message_ids[message] = i

    def create_message(self, message: ProtobufMessage) -> "ExonumMessage":
        """Method to convert a Protobuf message into an Exonum message.

        Parameters
        ----------
        message: google.protobuf.message.Message
            A Protobuf message.

        Returns
        -------
        exonum_message: ExonumMessage
            Exonum message object.
        """

        tx_name = type(message).__name__
        return ExonumMessage(self._instance_id, self._message_ids[tx_name], message)


class ExonumMessage:
    """Generic Exonum transaction class.

    Exonum message can be created:
     - by using MessageGenerator (if you want to send a transaction to the Exonum blockchain)
     - by using ExonumMessage.from_hex (if you want to parse a retrieved transaction).

    Example workflow:

    Sending a message:

    >>> instance_id = ... # Get the ID of the desired service instance.
    >>> artifact_name = ... # Get the name of the artifact (not the instance).
    >>> cryptocurrency_message_generator = MessageGenerator(instance_id, artifact_name) # Create a message generator.
    >>> create_wallet_alice = cryptocurrency_module.CreateWallet() # Create a Protobuf message.
    >>> create_wallet_alice.name = "Alice1" # Fill the Protobuf message manually.
    >>> create_wallet_alice_tx = cryptocurrency_message_generator.create_message(create_wallet_alice)
    >>> create_wallet_alice_tx.sign(keypair) # You should sign the message before sending.
    >>> client.send_transaction(create_wallet_alice_tx)

    Parsing a message:

    >>> message_hex = ... # Retrieve the message as a hexadecimal string.
    >>> artifact_name = ... # Get the name of the artifact (not the instance).
    >>> transaction_name = "CreateWallet" # Get the name of the transaction.
    >>> parsed_message = ExonumMessage.from_hex(message_hex, artifact_name, transaction_name)
    >>> assert parsed_message.validate() # Verify the signature of the retrieved message.

    Other methods:
    >>> message = ExonumMessage.from_hex(...)
    >>> author = message.author() # Get the author's public key.
    >>> tx_hash = message.hash() # Get the transaction hash.
    >>> signature = message.signature() # Get the transaction signature.
    >>> any_tx_raw = message.any_tx_raw() # Get AnyTx of the message serialized to bytes.
    >>> signed_tx_raw = message.signed_tx_raw() # Get SignedMessage of the message serialized to bytes.
    >>> tx_json = message.pack_into_json() # Create a JSON with the transaction in the format expected by Exonum.
    """

    def __init__(self, instance_id: int, message_id: int, msg: ProtobufMessage, prebuilt: Optional[bytes] = None):
        """Exonum message constructor. It is not intended to be used directly, see `MessageGenerator.create_message`
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

        # If we parse the received message, we do not have to build anything.
        if prebuilt is None:
            self._any_tx_raw = self._build_message()
        else:
            self._any_tx_raw = prebuilt

    @classmethod
    def from_hex(cls, message_hex: str, artifact_name: str, tx_name: str) -> Optional["ExonumMessage"]:
        """Attempts to parse an Exonum message from a serialized hexadecimal string.

        Parameters
        ----------
        message_hex: str
            Serialized message as a hexadecimal string.
        artifact_name: str
            The name of the service artifact you want to communicate with.
            The name should be in the format provided by Exonum, like 'exonum-cryptocurrency-advanced:0.12.0'.
        tx_name: str
            The name of the transaction to be parsed, e.g. 'CreateWallet'.

        Returns
        -------
        parsed_message: Optional[ExonumMessage]
            If parsing is successfull, an ExonumMessage object is returned.
            Otherwise the returned value is None.
        """
        try:
            signed_msg, exonum_msg, decoded_msg = cls._deserialize_message(message_hex, artifact_name, tx_name)

            service_id = exonum_msg.any_tx.call_info.instance_id
            message_id = exonum_msg.any_tx.call_info.method_id
            signature = signed_msg.signature.data[:]
            author = signed_msg.author.data[:]

            exonum_message = cls(service_id, message_id, decoded_msg, prebuilt=exonum_msg.any_tx.SerializeToString())

            cls._set_signature_data(exonum_message, author, signature, bytes.fromhex(message_hex))
            logger.debug(
                "Exonum message (ID: %s) from the service artifact '%s' " "for transaction '%s' parsed successfully.",
                message_id,
                artifact_name,
                tx_name,
            )
            return exonum_message
        except ProtobufDecodeError as e:
            logger.error(
                "Failed to parse an Exonum message from the service artifact '%s' " "for transaction '%s'. Error: %s.",
                artifact_name,
                tx_name,
                str(e),
            )
            return None

    def sign(self, keys: KeyPair) -> None:
        """Signs the message with the provided pair of keys.

        Please note that signing is required before sending a message to the Exonum blockchain.

        Parameters
        ----------
        keys: exonum.crypto.KeyPair
            A pair of public_key and secret_key as bytes.
        """

        public_key, secret_key = keys.public_key, keys.secret_key
        self._author = public_key

        consensus_mod = ModuleManager.import_main_module("consensus")
        types_mod = ModuleManager.import_main_module("types")

        signed_message = consensus_mod.SignedMessage()
        signed_message.payload = self._any_tx_raw
        signed_message.author.CopyFrom(types_mod.PublicKey(data=public_key.value))

        signature = Signature.sign(signed_message.payload, secret_key)

        signed_message.signature.CopyFrom(types_mod.Signature(data=signature.value))

        self._signature = signature

        self._signed_tx_raw = bytes(signed_message.SerializeToString())

        logger.debug(
            "Successfully signed the message (message ID: %s, service instance ID: %s): public_key='%s'.",
            self._message_id,
            self._instance_id,
            public_key,
        )

    def validate(self) -> bool:
        """
        Validates the message.
        Checks if the transaction signature is correct.
        :return: bool
        """
        if self._signature is None or self._author is None:
            return False

        try:
            consensus_mod = ModuleManager.import_main_module("consensus")

            signed_msg = consensus_mod.SignedMessage()
            signed_msg.ParseFromString(self._signed_tx_raw)

            return self._signature.verify(signed_msg.payload, self._author)
        except (ProtobufDecodeError, ValueError) as e:
            logger.error(
                "Failed to parse Exonum message (message ID: %s, service instance ID: %s): public_key='%s'. Error: %s",
                self._message_id,
                self._instance_id,
                self._author,
                str(e),
            )
            return False

    def pack_into_json(self) -> str:
        """Packs a serialized signed message into the JSON format expected by Exonum.

        Please note that this method does not serialize the message to JSON.

        Returns
        -------
        json_message: str
            String with a JSON representation of the serialized message.

        Raises
        ------
        RuntimeError
            An error will be raised on attempt to call `pack_into_json` with an unsigned message.
        """
        if self._signed_tx_raw is None:
            logger.critical("Attempt to call `to_json` on an unsigned message into JSON format.")
            raise RuntimeError("Attempt to pack an unsigned message.")
        return json.dumps({"tx_body": self._signed_tx_raw.hex()}, indent=4)

    def hash(self) -> Hash:
        """Returns a hash of the message. If the message is not signed, a hash of an empty message will be returned."""
        return Hash.hash_data(self._signed_tx_raw)

    # Getters section.

    def author(self) -> Optional[PublicKey]:
        """Returns an author's public key. If the author is not set, returns None."""
        return self._author

    def signature(self) -> Optional[Signature]:
        """Returns a signature. If the message is not signed, returns None."""
        return self._signature

    def any_tx_raw(self) -> bytes:
        """Returns a serialized AnyTx message as bytes."""
        return self._any_tx_raw

    def signed_raw(self) -> Optional[bytes]:
        """Returns a serialized SignedMessage as bytes. If the message is not signed, returns None."""
        return self._signed_tx_raw

    def _set_signature_data(self, author: bytes, signature: bytes, raw: bytes) -> None:
        self._author = PublicKey(author)
        self._signature = Signature(signature)
        self._signed_tx_raw = raw

    def _build_message(self) -> bytes:
        """Builds a raw AnyTx message."""
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

        # Load modules and prepare an expected message class for parsing.
        consensus_mod = ModuleManager.import_main_module("consensus")
        service_mod = ModuleManager.import_service_module(artifact_name, "service")
        transaction_class = getattr(service_mod, tx_name)

        # Convert a message from hex to bytes.
        tx_raw = bytes.fromhex(message_hex)

        # Parse SignedMessage.
        signed_msg = consensus_mod.SignedMessage()
        signed_msg.ParseFromString(tx_raw)

        # Parse ExonumMessage from the SignedMessage's payload.
        exonum_msg = consensus_mod.ExonumMessage()
        exonum_msg.ParseFromString(signed_msg.payload)

        # Parse an expected message from ExonumMessage's AnyTx arguments.
        decoded_msg = transaction_class()
        decoded_msg.ParseFromString(exonum_msg.any_tx.arguments)

        return signed_msg, exonum_msg, decoded_msg
