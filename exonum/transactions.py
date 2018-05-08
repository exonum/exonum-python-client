import struct

from pysodium import crypto_sign_detached, crypto_sign_BYTES as SIGNATURE_SZ

from .error import IllegalServiceId, NotEncodingStruct
from .datatypes import ExonumBase, EncodingStruct, u8, u16, u32


class Tx(metaclass=EncodingStruct):
    network_id = u8
    protocol_version = u8
    message_id = u16
    service_id = u16
    payload_sz = u32
    payload_sz_offset = struct.calcsize("<BBHH")


def mk_tx(cls, **kwargs):
    tx_cls = EncodingStruct(
        'Tx{}'.format(cls.__name__),
        (Tx, ),
        {"body": cls})

    def tx(self, secret_key, hex=False):
        tx = tx_cls(**kwargs, payload_sz=0, body=self)

        buf = bytearray(tx.sz)
        tx.write(buf, 0)
        real_size = len(buf) + SIGNATURE_SZ
        struct.pack_into(tx.payload_sz.fmt,
                         buf,
                         tx.payload_sz_offset,
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
