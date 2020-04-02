"""Module with the Common Cryptography-assotiated Utils.

This module uses libsodium as a backend."""
from typing import Optional

from pysodium import (
    crypto_sign_keypair,
    crypto_sign_detached,
    crypto_sign_verify_detached,
    crypto_hash_sha256,
    crypto_hash_sha256_BYTES,
    crypto_sign_SECRETKEYBYTES,
    crypto_sign_PUBLICKEYBYTES,
    crypto_sign_BYTES,
)

_HASH_BYTES_LEN = crypto_hash_sha256_BYTES
_PUBLIC_KEY_BYTES_LEN = crypto_sign_PUBLICKEYBYTES
_SECRET_KEY_BYTES_LEN = crypto_sign_SECRETKEYBYTES
_SIGNATURE_BYTES_LEN = crypto_sign_BYTES

# Hack for generating documentation:
# Autodoc replaces "pysodium" with a mock dependency, and constans above are becoming mock objects.

# In this module classes are used as a storage and also contain verification.
# pylint: disable=too-few-public-methods


class _FixedByteArray:
    """Base class for types which store a bytes sequence of a fixed length."""

    def __init__(self, data: bytes, expected_len: int):
        if len(data) != expected_len:
            raise ValueError(f"Incorrect data length: expected {expected_len}, got {len(data)}.")

        self.value: bytes = bytes(data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _FixedByteArray):
            return False
        return self.value == other.value

    def __str__(self) -> str:
        return self.hex()

    def hex(self) -> str:
        """Returns a hex representation of the value."""
        return self.value.hex()


class Hash(_FixedByteArray):
    """Representation of a SHA-256 hash."""

    def __init__(self, hash_bytes: bytes):
        super().__init__(hash_bytes, _HASH_BYTES_LEN)

    @classmethod
    def hash_data(cls, data: Optional[bytes]) -> "Hash":
        """Calculates a hash of the provided bytes sequence and returns a Hash object.

        If `None` is provided, a hash of the empty sequence will be returned."""
        if data is not None:
            hash_bytes = crypto_hash_sha256(data)
        else:
            hash_bytes = crypto_hash_sha256(bytes())
        return cls(hash_bytes)


class PublicKey(_FixedByteArray):
    """Representation of a Ed25519 Public Key."""

    def __init__(self, key: bytes):
        super().__init__(key, _PUBLIC_KEY_BYTES_LEN)


class SecretKey(_FixedByteArray):
    """Representation of a Ed25519 Secret Key."""

    def __init__(self, key: bytes):
        super().__init__(key, _SECRET_KEY_BYTES_LEN)


class KeyPair:
    """Representation of a Ed25519 keypair."""

    def __init__(self, public_key: PublicKey, secret_key: SecretKey):
        # Check that public_key corresponds to the secret_key.
        # Since we use only the libsodium backend, it is normal to make this
        # check as presented.
        # libsodium secret key contains a public key inside.
        if secret_key.value[_PUBLIC_KEY_BYTES_LEN:] != public_key.value:
            raise ValueError("Public key doesn't correspond to the secret key.")

        self.public_key = public_key
        self.secret_key = secret_key

    @classmethod
    def generate(cls) -> "KeyPair":
        """Generates a new random keypair"""
        public_key, secret_key = crypto_sign_keypair()
        return cls(PublicKey(public_key), SecretKey(secret_key))


class Signature(_FixedByteArray):
    """Representation of a Ed25519 signature"""

    def __init__(self, signature: bytes):
        super().__init__(signature, _SIGNATURE_BYTES_LEN)

    @classmethod
    def sign(cls, data: bytes, key: SecretKey) -> "Signature":
        """Signs the provided bytes sequence with the provided secret key."""

        signature = crypto_sign_detached(data, key.value)

        return Signature(signature)

    def verify(self, data: bytes, key: PublicKey) -> bool:
        """Verifies the signature against the provided data and the public key."""

        try:
            crypto_sign_verify_detached(self.value, data, key.value)
            return True
        except ValueError:
            # ValueError is raised if verification fails.
            return False
