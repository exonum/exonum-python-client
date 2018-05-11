import struct

from pysodium import crypto_sign_detached, crypto_sign_BYTES as SIGNATURE_SZ

from .error import IllegalServiceId, NotEncodingStruct
from .datatypes import ExonumBase


def mk_tx(cls, **kwargs):
    header_fmt = "<BBHHI"
    header_sz = struct.calcsize(header_fmt)

    def tx(self, secret_key, hex=False):
        buf = bytearray(header_sz)
        self.extend_buffer(buf)
        real_size = len(buf) + SIGNATURE_SZ

        struct.pack_into(header_fmt,
                         buf,
                         0,
                         kwargs["network_id"],
                         kwargs["protocol_version"],
                         kwargs["message_id"],
                         kwargs["service_id"],
                         real_size)
        data = bytes(buf)
        signature = crypto_sign_detached(data, secret_key)
        if hex:
            return data + signature

        message = dict(
            **kwargs,
            signature=signature.hex(),
            body=self.plain())
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

        setattr(cls, "tx",
                mk_tx(cls,
                      network_id=self.network_id,
                      protocol_version=self.protocol_version,
                      message_id=len(self.tx),
                      service_id=self.service_id))

        self.tx.append(cls.__name__)
        return cls
