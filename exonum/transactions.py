import struct

from pysodium import crypto_sign_detached, crypto_sign_BYTES
from codecs import encode

from . import ExonumException
from .datatypes import ExonumBase


class NotEncodingStruct(ExonumException):
    pass


class IllegalServiceId(ExonumException):
    pass


class NotImplementedYet(ExonumException):
    pass


def mk_tx(network_id, protocol_version, message_id, serivce_id):
    def tx(self, secret_key, hex=False):
        fmt = "<BBHHI"
        header_len = struct.calcsize(fmt)
        buf = bytearray(header_len + self.sz)
        self.write(buf, header_len)
        buf_sz = len(buf)
        struct.pack_into(fmt,
                         buf,
                         0,
                         network_id,
                         protocol_version,
                         message_id,
                         serivce_id,
                         buf_sz + crypto_sign_BYTES)
        data = bytes(buf)
        signature = crypto_sign_detached(data, secret_key)

        if hex:
            return data + signature

        message = {
            "network_id": network_id,
            "protocol_version": protocol_version,
            "service_id": serivce_id,
            "message_id": message_id,
            "signature": signature.hex(),
            "body": self.plain()
        }

        return message

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
