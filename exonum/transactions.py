# coding: utf-8
import codecs
import struct
from copy import copy
from itertools import chain

from pysodium import crypto_sign_BYTES as SIGNATURE_SZ
from pysodium import crypto_sign_detached

from .datatypes import EncodingStruct, ExonumBase, TxHeader
from .error import IllegalServiceId, NotEncodingStruct


def mk_tx(cls, **kwargs):
    header_fmt = "<BBHHI"
    header_sz = struct.calcsize(header_fmt)

    def tx(self, secret_key, hex=False):
        buf = bytearray(header_sz)
        self.extend_buffer(buf)
        real_size = len(buf) + SIGNATURE_SZ

        struct.pack_into(
            header_fmt,
            buf,
            0,
            kwargs["network_id"],
            kwargs["protocol_version"],
            kwargs["message_id"],
            kwargs["service_id"],
            real_size,
        )
        data = bytes(buf)
        signature = crypto_sign_detached(data, secret_key)
        if hex:
            return data + signature
        message = copy(kwargs)
        message["signature"] = codecs.encode(signature, "hex").decode("utf-8")
        message["body"] = self.plain()
        return message

    return tx


class transactions(object):
    def __init__(self, service_id=-1, protocol_version=0, network_id=0):
        if service_id < 0:
            raise IllegalServiceId()

        self.service_id = service_id
        self.protocol_version = protocol_version
        self.network_id = network_id
        self.tx = []

    @staticmethod
    def is_encoding_struct(cls):
        return isinstance(cls, type) and issubclass(cls, ExonumBase)

    def __call__(self, cls):
        if not self.is_encoding_struct(cls):
            raise NotEncodingStruct()

        tx = list(TxHeader)
        tx.extend((k, getattr(cls, k)) for k in chain(cls.__exonum_fields__))

        tx_cls = EncodingStruct(cls.__name__, (), {k: v() for k, v in tx})
        message_id = len(self.tx)

        class Tx(tx_cls):
            def __init__(tx_self, *args, **kwargs):
                if "message_id" not in kwargs:
                    kwargs["network_id"] = self.network_id
                    kwargs["protocol_version"] = self.protocol_version
                    kwargs["message_id"] = message_id
                    kwargs["service_id"] = self.service_id
                    kwargs["payload_sz"] = 0
                tx_cls.__init__(tx_self, *args, **kwargs)

            def tx(self, secret_key, hex=False):
                data = bytearray(0)
                self.extend_buffer(data)
                sz = len(data) + SIGNATURE_SZ
                struct.pack_into("<i", data, 6, sz)
                data = bytes(data)

                signature = crypto_sign_detached(data, secret_key)

                if hex:
                    return data + signature

                meta_fields = {k for (k, _) in TxHeader}
                plain = self.plain()
                message = {k: plain[k] for k in meta_fields}
                message["signature"] = codecs.encode(signature, "hex").decode("utf-8")
                message["body"] = {
                    k: v for k, v in plain.items() if k not in meta_fields
                }
                del message["payload_sz"]
                return message

        self.tx.append(cls.__name__)
        return Tx
