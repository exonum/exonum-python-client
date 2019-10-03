"""This module is capable of creating and signing Exonum transactions."""

from typing import Dict, Optional
import json
import struct

from google.protobuf.message import Message as ProtobufMessage, DecodeError as ProtobufDecodeError

from .crypto import PublicKey, Hash, Signature, KeyPair
from .module_manager import ModuleManager


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

    def __init__(self, instance_id: int, artifact_name: str, module_name: str):
        """MessageGenerator constructor.

        Parameters
        ----------
        instance_id: int
            ID of the desired Exonum service instance.
        artifact_name: str
            The name of the service artifact you want to communicate with (e.g. 'cryptocurrency-advanced').
        module_name: str
            The name of the .proto file (e.g. "cryptocurrency") to load messages from.
        """
        self._instance_id = instance_id

        self._artifact_name = artifact_name
        self._message_ids: Dict[str, int] = dict()

        service_module = ModuleManager.import_service_module(artifact_name, module_name)
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

    _MINIMUM_TX_BODY_LENGTH = 102  # It calculated as first 38 metadata bytes plus signature with 64 bytes length
    _PUBLIC_KEY_LENGTH = 32
    _SIGNATURE_LENGTH = 64
    _SERVICE_ID_START_POSITION = 34
    _MESSAGE_ID_START_POSITION = 36
    _PROTO_MESSAGE_START_POSITION = 38
    _U16_LENGTH = 2

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
            self._unsigned_tx_raw = self._build_message()
        else:
            self._unsigned_tx_raw = prebuilt

    @classmethod
    def from_hex(
        cls, message_hex: str, artifact_name: str, module_name: str, tx_name: str
    ) -> Optional["ExonumMessage"]:
        """Attempts to parse Exonum Message from serialized hexadecimal string.

        Parameters
        ----------
        message_hex: str
            Serialized message as a hexadecimal string.
        artifact_name: str
            The name of the service artifact you want to communicate with (e.g. 'cryptocurrency-advanced').
        module_name: str
            The name of the .proto file (e.g. "cryptocurrency") to load messages from.
        tx_name: str
            The name of the transaction to be parsed, e.g. 'CreateWallet'.

        Returns
        -------
        parsed_message: Optional[ExonumMessage]
            If parsing is successfull, an ExonumMessage object is returned.
            Otherwise the returned value is None.
        """
        # Load modules and prepare expected message class for parsing.
        service_mod = ModuleManager.import_service_module(artifact_name, module_name)
        transaction_class = getattr(service_mod, tx_name)

        # Convert message from hex to bytes.
        tx_raw = bytes.fromhex(message_hex)

        # Parse data.
        if len(tx_raw) < cls._MINIMUM_TX_BODY_LENGTH:
            return None
        try:
            author = tx_raw[: cls._PUBLIC_KEY_LENGTH]
            service_id = struct.unpack(
                "<H", tx_raw[cls._SERVICE_ID_START_POSITION : cls._SERVICE_ID_START_POSITION + cls._U16_LENGTH]
            )[0]
            message_id = struct.unpack(
                "<H", tx_raw[cls._MESSAGE_ID_START_POSITION : cls._MESSAGE_ID_START_POSITION + cls._U16_LENGTH]
            )[0]
            signature = tx_raw[-cls._SIGNATURE_LENGTH :]

            decoded_msg = transaction_class()
            decoded_msg.ParseFromString(tx_raw[cls._PROTO_MESSAGE_START_POSITION : -cls._SIGNATURE_LENGTH])
        except (ValueError, IndexError, ProtobufDecodeError):
            return None

        # Create the message.
        try:
            exonum_message = cls(service_id, message_id, decoded_msg)
            cls._set_signature_data(exonum_message, author, signature, tx_raw)

            return exonum_message
        except ValueError:
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

        signed_raw = bytearray()

        signed_raw.extend(public_key.value)
        signed_raw.extend(struct.pack("<B", 0))  # 0 and 0 it's tag and class of TX message
        signed_raw.extend(struct.pack("<B", 0))
        signed_raw.extend(struct.pack("<H", self._instance_id))
        signed_raw.extend(struct.pack("<H", self._message_id))
        signed_raw.extend(self._unsigned_tx_raw)

        signature = Signature.sign(bytes(signed_raw), secret_key)

        signed_raw.extend(signature.value)

        self._signature = signature

        self._signed_tx_raw = bytes(signed_raw)

    def validate(self) -> bool:
        """
        Validates the message.
        Checks if the transaction signature is correct.
        :return: bool
        """
        if self._signature is None or self._author is None or self._signed_tx_raw is None:
            return False

        try:
            return self._signature.verify(self._signed_tx_raw[: -self._SIGNATURE_LENGTH], self._author)
        except (ProtobufDecodeError, ValueError, IndexError):
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
            raise RuntimeError("Attempt to call `to_json` on an unsigned message.")
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

    def unsigned_raw(self) -> bytes:
        """Returns a serialized unsigned message as bytes."""
        return self._unsigned_tx_raw

    def signed_raw(self) -> Optional[bytes]:
        """Returns a serialized SignedMessage as bytes. If the message is not signed, returns None."""
        return self._signed_tx_raw

    def _set_signature_data(self, author: bytes, signature: bytes, raw: bytes) -> None:
        self._author = PublicKey(author)
        self._signature = Signature(signature)
        self._signed_tx_raw = raw

    def _build_message(self) -> bytes:
        """Builds a raw (unsigned) message."""
        return self._msg.SerializeToString()
