"""Tests for the Crypto Module."""
# pylint: disable=missing-docstring, protected-access
# type: ignore

import unittest

from pysodium import (
    crypto_sign_detached,
    crypto_hash_sha256,
    crypto_hash_sha256_BYTES,
    crypto_sign_SECRETKEYBYTES,
    crypto_sign_PUBLICKEYBYTES,
    crypto_sign_BYTES,
)

from exonum_client.crypto import (
    _FixedByteArray,
    Hash,
    Signature,
    PublicKey,
    SecretKey,
    KeyPair,
    HASH_BYTES_LEN,
    PUBLIC_KEY_BYTES_LEN,
    SECRET_KEY_BYTES_LEN,
    SIGNATURE_BYTES_LEN,
)


class TestFixedByteArray(unittest.TestCase):
    """ Tests for the _FixedByteArray class. """

    def test_creation(self) -> None:
        """Tests that object is created as expected."""
        length = 10
        data = bytes([i for i in range(length)])

        # Check that the object is created as expected based on the correct data:
        array = _FixedByteArray(data, length)
        self.assertEqual(array.value, data)

        # Check that an attempt to create an object with incorrect data raises an error:
        with self.assertRaises(ValueError):
            _FixedByteArray(data, length - 1)

    def test_eq(self) -> None:
        """Tests that __eq__ method works as expected."""
        length = 10
        data_1 = bytes([i for i in range(length)])
        data_2 = bytes([i for i in range(length)])

        array_1 = _FixedByteArray(data_1, length)
        array_2 = _FixedByteArray(data_2, length)

        self.assertEqual(array_1, array_2)
        self.assertNotEqual(array_1, [])
        self.assertNotEqual(array_1, data_1)

    def test_str(self) -> None:
        """Tests that __str__ method works as expected."""
        length = 10
        data = bytes([i for i in range(length)])

        array = _FixedByteArray(data, length)

        self.assertEqual(str(array), data.hex())


class TestCrypto(unittest.TestCase):
    """Tests for all the classes in the Crypto module."""

    def test_constants(self) -> None:
        """Tests that constants have appropriate values."""
        expected_values = [
            [HASH_BYTES_LEN, crypto_hash_sha256_BYTES],
            [PUBLIC_KEY_BYTES_LEN, crypto_sign_PUBLICKEYBYTES],
            [SECRET_KEY_BYTES_LEN, crypto_sign_SECRETKEYBYTES],
            [SIGNATURE_BYTES_LEN, crypto_sign_BYTES],
        ]

        for value, expected in expected_values:
            self.assertEqual(value, expected)

    def test_hash(self) -> None:
        """Tests the Hash class."""
        raw_hash = bytes([0xAB for _ in range(HASH_BYTES_LEN)])
        hash_obj = Hash(raw_hash)

        self.assertTrue(isinstance(hash_obj, _FixedByteArray))

        self.assertEqual(hash_obj.value, raw_hash)
        self.assertEqual(hash_obj.hex(), raw_hash.hex())
        self.assertEqual(Hash.hash_data(bytes()), Hash(crypto_hash_sha256(bytes())))
        self.assertEqual(Hash.hash_data(bytes([1, 2])), Hash(crypto_hash_sha256(bytes([1, 2]))))

    def test_keys(self) -> None:
        """Tests the PublicKey and the SecretKey classes."""
        data = bytes([i for i in range(PUBLIC_KEY_BYTES_LEN)])

        public_key = PublicKey(data)
        self.assertTrue(isinstance(public_key, _FixedByteArray))
        self.assertEqual(public_key.value, data)

        data = bytes([i for i in range(SECRET_KEY_BYTES_LEN)])

        secret_key = SecretKey(data)
        self.assertTrue(isinstance(secret_key, _FixedByteArray))
        self.assertEqual(secret_key.value, data)

    def test_keypair(self) -> None:
        """Tests the KeyPair class."""
        public_key = PublicKey(bytes([i for i in range(PUBLIC_KEY_BYTES_LEN)]))
        secret_key = SecretKey(bytes([i for i in range(SECRET_KEY_BYTES_LEN)]))

        # Check that creation with unmatched keys raises an error:
        with self.assertRaises(ValueError):
            KeyPair(public_key, secret_key)

        # Check that generation of the keypair works:
        keypair = KeyPair.generate()
        self.assertTrue(isinstance(keypair.public_key, PublicKey))
        self.assertTrue(isinstance(keypair.secret_key, SecretKey))
        self.assertNotEqual(keypair.public_key, keypair.secret_key)
        self.assertEqual(keypair.secret_key.value[PUBLIC_KEY_BYTES_LEN:], keypair.public_key.value)

        # Check that creating a keypair from the matched keys works:
        _new_keypair = KeyPair(keypair.public_key, keypair.secret_key)

    def test_signature(self) -> None:
        """Tests the Signature class."""
        keypair = KeyPair.generate()

        data = bytes([i for i in range(10)])

        signature = Signature.sign(data, keypair.secret_key)

        self.assertTrue(isinstance(signature, Signature))
        self.assertTrue(isinstance(signature, _FixedByteArray))
        self.assertEqual(signature.value, crypto_sign_detached(data, keypair.secret_key.value))

        self.assertTrue(signature.verify(data, keypair.public_key))

        wrong_data = bytes([1, 2])
        wrong_pk = PublicKey(bytes([i for i in range(PUBLIC_KEY_BYTES_LEN)]))
        self.assertFalse(signature.verify(wrong_data, keypair.public_key))
        self.assertFalse(signature.verify(data, wrong_pk))
