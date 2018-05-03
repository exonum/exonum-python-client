import sys

from .util import make_class_ordered
from .datatypes import ExonumBase
from . import ExonumException

from pysodium import crypto_sign_keypair, crypto_sign_detached, crypto_hash_sha256
import struct

SIGNATURE_LEN = 64

class NotEncodingStruct(ExonumException):
    pass


class IllegalServiceId(ExonumException):
    pass


class NotImplementedYet(ExonumException):
    pass


def mk_tx(network_id, protocol_version, message_id, serivce_id):
    def tx(self, secret_key):
        fmt = "<BBHHI"
        data_len = self.sz + struct.calcsize(fmt) + SIGNATURE_LEN
        data = struct.pack(fmt,
                           network_id,
                           protocol_version,
                           message_id,
                           serivce_id,
                           data_len) + self.to_bytes()
        signature = crypto_sign_detached(data, secret_key)

        print(signature.hex(), len(signature))

    return tx


class transactions():
    def __init__(self,
                 service_id=-1,
                 protocol_version=0,
                 network_id=0):
        if service_id < 0:
            raise IllegalServiceId()

        self.service_id = service_id
        self.protocol_version = protocol_version
        self.network_id = network_id
        self.tx = []

    @staticmethod
    def is_encoding_struct(cls):
        return (isinstance(cls, type)
                and issubclass(cls, ExonumBase))

    def __call__(self, cls):
        if not self.is_encoding_struct(cls):
            raise NotEncodingStruct()

        setattr(cls, "tx", mk_tx(self.network_id,
                                 self.protocol_version,
                                 len(self.tx),
                                 self.service_id))

        self.tx.append(cls.__name__)
        return cls
