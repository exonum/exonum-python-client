# coding: utf-8
import codecs
import decimal
import ipaddress
import logging
import struct
from datetime import datetime
from itertools import count
from uuid import UUID

import nanotime
import six

from ._decimal import ctx as decimal_ctx
from ._decimal import from_bytes as decimal_from_bytes
from ._decimal import to_bytes as decimal_to_bytes
from .error import (
    CantComare,
    NotImplementedYet,
    NotSupported,
    UnsupportedDatatype,
    IllegalUsage,
)

log = logging.getLogger("exonum datatypes")
dbg = log.debug


@six.python_2_unicode_compatible
class ExonumField(object):
    sz = 1
    fmt = None
    _counter = count()

    def _set_order(self):
        self._order = next(ExonumField._counter)

    def __init__(self, *val):
        if len(val) == 0:
            self._set_order()
            return
        self.val = val[0]

    def __eq__(self, other):
        return (
            hasattr(other, "__class__")
            and self.__class__ == other.__class__
            and hasattr(other, "val")
            and self.val == other.val
        ) or (self.val == other)

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def read(cls, buf, offset=0):
        val, = struct.unpack_from(cls.fmt, buf, offset=offset)
        return cls(val)

    def write(self, buf, offset):
        raw = struct.pack(self.fmt, self.val)
        buf[offset : offset + self.sz] = raw

    def __str__(self):
        return u"{}({})".format(self.__class__.__name__, self.val)

    def plain(self):
        return self.val


class ExonumSegment(ExonumField):
    sz = 8
    fmt = "<2I"
    T = None

    def write(self, buf, offset):
        dbg("writing {} at offset {}".format(self, offset))
        end = offset + self.sz
        start = len(buf)

        self.extend_buffer(buf)

        size = len(buf) - start
        buf[offset:end] = struct.pack(self.fmt, start, size)

    @classmethod
    def read(cls, buf, offset=0):
        segm_offset, cnt = struct.unpack_from(cls.fmt, buf, offset=offset)
        dbg("Segment {} lays at position = {} count = {}".format(cls, segm_offset, cnt))
        return cls.read_buffer(buf, offset=segm_offset, cnt=cnt)


class bool(ExonumField):
    fmt = "<B"


class u8(ExonumField):
    fmt = "<B"


class u16(ExonumField):
    sz = 2
    fmt = "<H"


class u32(ExonumField):
    sz = 4
    fmt = "<I"


class ExonumBigInt(ExonumField):
    sz = None
    fmt = None

    def __init__(self, *val):
        if len(val) == 0:
            self._set_order()
            return
        self.val = int(val[0])

    def plain(self):
        return "{}".format(self.val)


class u64(ExonumBigInt):
    sz = 8
    fmt = "<Q"


class i8(ExonumField):
    fmt = "<b"


class i16(ExonumField):
    sz = 2
    fmt = "<h"


class i32(ExonumField):
    sz = 4
    fmt = "<i"


class i64(ExonumBigInt):
    sz = 8
    fmt = "<q"


@six.python_2_unicode_compatible
class Hash(ExonumField):
    sz = 32
    fmt = "32s"

    def __str__(self):
        return u"{}({})".format(self.__class__.__name__, self.plain())

    def plain(self):
        return codecs.encode(self.val, "hex").decode("utf-8")


class PublicKey(Hash):
    pass


class Signature(Hash):
    sz = 64
    fmt = "64s"


class DateTime(ExonumField):
    sz = 12
    fmt = "<qI"

    def __init__(self, *val):
        if len(val) == 0:
            self._set_order()
            return
        val = val[0]
        if isinstance(val, (float, int)):
            self.val = nanotime.timestamp(val)
        elif isinstance(val, datetime):
            self.val = nanotime.datetime(val)
        elif isinstance(val, nanotime.nanotime):
            self.val = val
        elif isinstance(val, dict) and "nanos" in val and "secs" in val:
            self.val = nanotime.seconds(int(val["secs"])) + nanotime.nanoseconds(
                int(val["nanos"])
            )
        else:
            raise UnsupportedDatatype(
                "Type {} is not supported for initializing DateTime".format(type(val))
            )

    def __eq__(self, other):
        return (
            hasattr(other, "__class__")
            and self.__class__ == other.__class__
            and hasattr(other, "val")
            and self.val.nanoseconds() == other.val.nanoseconds()
        ) or (self.val == other)

    def to_pair(self):
        sec = int(self.val.seconds())
        nan = (self.val - nanotime.seconds(sec)).nanoseconds()
        return sec, nan

    def write(self, buf, offset):
        sec, nan = self.to_pair()
        raw = struct.pack(self.fmt, sec, nan)
        buf[offset : offset + self.sz] = raw

    @classmethod
    def read(cls, buf, offset=0):
        sec, nan = struct.unpack_from(cls.fmt, buf, offset=offset)
        return cls(nanotime.seconds(sec) + nanotime.nanoseconds(nan))

    def plain(self):
        sec, nan = self.to_pair()
        return {"secs": "{}".format(sec), u"nanos": nan}


class Uuid(ExonumField):
    sz = 16
    fmt = "<16B"

    def __init__(self, *val):
        if len(val) == 0:
            self._set_order()
            return
        val = val[0]
        if isinstance(val, UUID):
            self.val = val
        else:
            self.val = UUID(val)

    def write(self, buf, offset):
        buf[offset : offset + self.sz] = self.val.bytes

    @classmethod
    def read(cls, buf, offset=0):
        return cls(UUID(bytes=buf[offset : offset + cls.sz]))

    def plain(self):
        return self.val.hex


class Decimal(ExonumField):
    sz = 16
    fmt = "<4I"

    def __init__(self, *val):
        if len(val) == 0:
            self._set_order()
            return
        val = val[0]
        if not isinstance(val, decimal.Decimal):
            self.val = decimal_ctx.create_decimal(val)
        else:
            self.val = val

    def write(self, buf, offset):
        end = offset + self.sz
        buf[offset:end] = struct.pack(self.fmt, *decimal_to_bytes(self.val))

    @classmethod
    def read(cls, buf, offset=0):
        data = struct.unpack_from(cls.fmt, buf, offset=offset)
        val = decimal_from_bytes(*data)
        return cls(decimal.Decimal(val))

    def plain(self):
        return u"{}".format(self.val)


class SocketAddr(ExonumField):
    sz = 6
    fmt = "<4BH"

    def __init__(self, *val):
        if len(val) == 0:
            self._set_order()
            return
        val = val[0]

        ip = val[0]
        if not isinstance(val[0], ipaddress.IPv4Address):
            ip = ipaddress.IPv4Address(val[0])

        self.val = (ip, val[1])

    def write(self, buf, offset):
        raw = self.val[0].packed + struct.pack("<H", self.val[1])

        buf[offset : offset + self.sz] = raw

    @classmethod
    def read(cls, buf, offset=0):
        # dbg(data[])
        data = struct.unpack_from(cls.fmt, buf, offset=offset)
        return cls(["{}.{}.{}.{}".format(*data), data[-1]])

    def plain(self):
        raise NotImplementedYet(self.__class__)


class Str(ExonumSegment):
    def count(self):
        return len(self.val.encode("utf-8"))

    def extend_buffer(self, buf):
        buf += self.val.encode("utf-8")

    @classmethod
    def read_buffer(cls, buf, offset=0, cnt=0):
        return cls(buf[offset : offset + cnt].decode("utf-8"))

    def plain(self):
        return self.val


@six.python_2_unicode_compatible
class Vector(ExonumSegment):
    def __init__(self, *val):
        if len(val) == 0:
            self._set_order()
            return
        val = val[0]

        if isinstance(val[0], self.T):
            self.val = val
        else:
            self.val = [self.T(x) for x in val]

    def count(self):
        return len(self.val)

    def __getitem__(self, i):
        return self.val.__getitem__(i)

    def __str__(self):
        repr = ["{}".format(i) for i in self.val]
        return "{} [{}]".format(self.__class__.__name__, ", ".join(repr))

    @classmethod
    def read_buffer(cls, buf, offset=0, cnt=0):
        dbg("reading vector of sz {}".format(cnt))
        v = []
        for _ in range(cnt):
            t = cls.T.read(buf, offset=offset)
            dbg("read {} at offset {}".format(t, offset))
            v.append(t)
            offset += cls.T.sz
        return cls(v)

    def write(self, buf, offset):
        dbg(
            "writing vector ({}) of sz {} at offset {}".format(
                self.T.__name__, self.count(), offset
            )
        )

        buf[offset : offset + self.sz] = struct.pack(self.fmt, len(buf), self.count())
        self.extend_buffer(buf)

    def extend_buffer(self, buf):
        offset = len(buf)
        buf += bytearray(self.count() * self.T.sz)

        for x in self.val:
            x.write(buf, offset)
            offset += self.T.sz

    def plain(self):
        return [i.plain() for i in self.val]


def Vec(T):
    if issubclass(T, ExonumField):
        return type("Vec<{}>".format(T.__name__), (Vector,), {"T": T})()
    raise NotSupported()


@six.python_2_unicode_compatible
class Opt(ExonumSegment):
    def __init__(self, *val):
        if len(val) == 0:
            self._set_order()
            return

        val = val[0]
        if val:
            if isinstance(val, self.T):
                self.val = val
            else:
                self.val = self.T(val)
        else:
            self.val = None

    def count(self):
        return 1 if self.val else 0

    def __str__(self):
        v = self.val
        repr = "{}".format(v) if v else "None"
        return "{} [{}]".format(self.__class__.__name__, ", ".join(repr))

    @classmethod
    def read_buffer(cls, buf, offset=0, cnt=0):
        dbg("reading Opt of sz {}".format(cnt))
        if cnt == 1:
            t = cls.T.read(buf, offset=offset)
            dbg("read {} at offset {}".format(t, offset))
            return cls(t)
        else:
            assert cnt == 0, "One argument expected"
            return cls(None)

    def write(self, buf, offset):
        dbg(
            "writing Opt ({}) of sz {} at offset {}".format(
                self.T.__name__, self.count(), offset
            )
        )
        buf[offset : offset + self.sz] = struct.pack(self.fmt, len(buf), self.count())
        self.extend_buffer(buf)

    def extend_buffer(self, buf):
        offset = len(buf)
        buf += bytearray(self.count() * self.T.sz)
        if self.val:
            self.val.write(buf, offset)
            offset += self.T.sz

    def plain(self):
        if self.val:
            return self.val.plain()
        else:
            return None


def Option(T):
    if issubclass(T, ExonumField):
        return type("Option<{}>".format(T.__name__), (Opt,), {"T": T})()
    raise NotSupported()


class ExonumBase(ExonumSegment):
    def count(self):
        return self.cnt

    def __init__(self, val=None, **kwargs):
        if val is None and len(kwargs) == 0:
            self._set_order()
            return

        self.cnt = 0

        for field in self.__exonum_fields__:
            cls = getattr(self.__class__, field)
            field_ = kwargs[field]
            if not isinstance(field_, cls):
                field_ = cls(field_)
            self.cnt += field_.sz
            if issubclass(cls, ExonumSegment):
                self.cnt += field_.count()
            setattr(self, field, field_)

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            raise CantComare(self.__class__, other.__class__)
        for field in self.__exonum_fields__:
            if getattr(self, field) != getattr(other, field):
                return False
        return True

    def extend_buffer(self, buf):
        tmp = bytearray(self.fields_sz)
        offset = 0
        for field in self.__exonum_fields__:
            field = getattr(self, field)
            field.write(tmp, offset)
            offset += field.sz

        buf += tmp

    def __str__(self):
        repr = []
        for field in self.__exonum_fields__:
            repr.append(u"{} = {}".format(field, getattr(self, field)))
        return u"{} ({})".format(self.__class__.__name__, u", ".join(repr))

    @classmethod
    def read(cls, buf, offset=0):
        offset, cnt = struct.unpack_from(cls.fmt, buf, offset=offset)
        dbg("{} lays at position = {} count = {}".format(cls, offset, cnt))
        return cls.read_buffer(buf[offset : offset + cnt])

    @classmethod
    def read_buffer(cls, buf, offset=0, cnt=None):
        if cnt is None:
            cnt = len(buf)
        segment = buf[offset : offset + cnt]
        dbg("read_buffer of ExonumBase sz {}".format(cls.sz))
        offset = 0
        data = {}
        for field in cls.__exonum_fields__:
            fcls = getattr(cls, field)
            dbg("trying to read {} {} at offset {}".format(field, fcls, offset))
            val = fcls.read(segment, offset)
            offset += fcls.sz

            data[field] = val
        return cls(**data)

    def to_bytes(self):
        b = bytearray()
        self.extend_buffer(b)
        return bytes(b)

    def plain(self):
        return {k: getattr(self, k).plain() for k in self.__exonum_fields__}


class EncodingStruct(type):
    def __new__(self, name, bases, classdict):
        fields = []
        sz = 0

        for k, v in six.iteritems(classdict):
            if isinstance(v, type) and issubclass(v, ExonumField):
                raise IllegalUsage(
                    "{}: {} - "
                    "One cant use ExonumField this way.\n"
                    "You should initialize it in class definition.\n"
                    "ex: {} = {}()".format(name, k, k, v.__name__)
                )

            if isinstance(v, ExonumField):
                classdict[k] = v.__class__
                fields.append((k, v))
                sz += v.sz

        fields.sort(key=lambda v: v[1]._order)
        classdict["__exonum_fields__"] = [k for k, _ in fields]
        classdict["fields_sz"] = sz

        # py2 compat
        _bases = list(bases)
        _bases.insert(0, ExonumBase)
        return type(name, tuple(_bases), classdict)


TxHeader = (
    ("network_id", u8),
    ("protocol_version", u8),
    ("message_id", u16),
    ("service_id", u16),
    ("payload_sz", u32),
)
