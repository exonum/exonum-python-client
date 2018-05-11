import ipaddress
import decimal
import struct
import sys

from datetime import datetime
from uuid import UUID

import nanotime

from itertools import chain

from .error import NotSupported, NotImplementedYet, CantComare, UnsupportedDatatype
from .decimal import (ctx as decimal_ctx,
                      to_bytes as decimal_to_bytes,
                      from_bytes as decimal_from_bytes)

import logging
log = logging.getLogger("exonum datatypes")
dbg = log.debug


class ExonumField:
    sz = 1
    fmt = None

    def __init__(self, val):
        self.val = val

    def __eq__(self, other):
        if hasattr(other, "val"):
            return self.val == other.val
        return self.val == other

    @classmethod
    def read(cls, buf, offset=0):
        val, =  struct.unpack_from(cls.fmt, buf, offset=offset)
        return cls(val)

    def write(self, buf, offset):
        raw = struct.pack(self.fmt, self.val)
        buf[offset: offset + self.sz] = raw

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.val)

    def plain(self):
        return self.val


class ExonumSegment(ExonumField):
    sz = 8
    fmt = "<2I"
    T = None

    def write(self, buf, offset):
        dbg("writing {} at offset {}".format(self, offset))
        end = offset + self.sz
        buf[offset: end] = struct.pack(self.fmt, len(buf), self.count())
        self.extend_buffer(buf)

    @classmethod
    def read(cls, buf, offset=0):
        offset, cnt = struct.unpack_from(cls.fmt, buf, offset=offset)

        dbg("{} lays at position = {} count = {}".format(cls, offset, cnt))
        return cls.read_buffer(buf, offset, cnt)


class bool(ExonumField):
    fmt = '<B'


class u8(ExonumField):
    fmt = '<B'


class u16(ExonumField):
    sz = 2
    fmt = '<H'


class u32(ExonumField):
    sz = 4
    fmt = '<I'


class u64(ExonumField):
    sz = 8
    fmt = '<Q'


class i8(ExonumField):
    fmt = '<b'


class i16(ExonumField):
    sz = 2
    fmt = '<h'


class i32(ExonumField):
    sz = 4
    fmt = '<i'


class i64(ExonumField):
    sz = 8
    fmt = '<q'


class Hash(ExonumField):
    sz = 32
    fmt = '32s'

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.val.hex())

    def plain(self):
        return self.val.hex()


class PublicKey(Hash):
    pass


class Signature(Hash):
    sz = 64
    fmt = '64s'


class DateTime(ExonumField):
    sz = 12
    fmt = '<qI'

    def __init__(self, val):
        if isinstance(val, (float, int)):
            self.val = nanotime.timestamp(val)
        elif isinstance(val, datetime):
            self.val = nanotime.datetime(val)
        elif isinstance(val, nanotime.nanotime):
            self.val = val
        elif (isinstance(val, dict)
              and "nanos" in val
              and "secs" in val):
            self.val = (nanotime.seconds(int(val["secs"]))
                        + nanotime.nanoseconds(int(val["nanos"])))
        else:
            raise UnsupportedDatatype(
                "Type {} is not supported for initializing DateTime"
                .format(type(val)))

    def to_pair(self):
        sec = int(self.val.seconds())
        nan = (self.val - nanotime.seconds(sec)).nanoseconds()
        return sec, nan

    def write(self, buf, offset):
        sec, nan = self.to_pair()
        raw = struct.pack(self.fmt, sec, nan)
        buf[offset: offset + self.sz] = raw

    @classmethod
    def read(cls, buf, offset=0):
        sec, nan = struct.unpack_from(cls.fmt, buf, offset=offset)
        return cls(nanotime.seconds(sec) + nanotime.nanoseconds(nan))

    def plain(self):
        sec, nan = self.to_pair()
        return {"secs": str(sec), "nanos": nan}


class Uuid(ExonumField):
    sz = 16
    fmt = "<16B"

    def __init__(self, val):
        if isinstance(val, UUID):
            self.val = val
        else:
            self.val = UUID(val)

    def write(self, buf, offset):
        buf[offset: offset + self.sz] = self.val.bytes

    @classmethod
    def read(cls, buf, offset=0):
        return cls(UUID(bytes=buf[offset: offset+cls.sz]))

    def plain(self):
        return self.val.hex


class Decimal(ExonumField):
    sz = 16
    fmt = "<4I"

    def __init__(self, val):
        if not isinstance(val, decimal.Decimal):
            self.val = decimal_ctx.create_decimal(val)
        else:
            self.val = val

    def write(self, buf, offset):
        end = offset + self.sz
        buf[offset: end] = struct.pack(self.fmt, *decimal_to_bytes(self.val))

    @classmethod
    def read(cls, buf, offset=0):
        data, = struct.unpack_from(cls.fmt, buf, offset=offset)
        val = decimal_from_bytes(*data)
        return cls(decimal.Decimal(val))

    def plain(self):
        return str(self.val)


class SocketAddr(ExonumField):
    sz = 6
    fmt = "<4BH"

    def __init__(self, val):
        ip = val[0]
        if not isinstance(val[0], ipaddress.IPv4Address):
            ip = ipaddress.IPv4Address(val[0])

        self.val = (ip, val[1])

    def write(self, buf, offset):
        raw = self.val[0].packed + struct.pack("<H", self.val[1])
        dbg(raw.hex())
        buf[offset: offset + self.sz] = raw


    @classmethod
    def read(cls, buf, offset=0):
        # dbg(data[])
        data = struct.unpack_from(cls.fmt, buf, offset=offset)
        return cls(["{}.{}.{}.{}".format(*data), data[-1]])

    def plain(self):
        raise NotImplementedYet(self.__class__)


class Str(ExonumSegment):
    def count(self):
        return len(self.val.encode())

    def extend_buffer(self, buf):
        buf += self.val.encode()

    @classmethod
    def read_buffer(cls, buf, offset, cnt):
        return cls(buf[offset: offset + cnt].decode("utf-8"))

    def plain(self):
        return self.val


class Vector(ExonumSegment):
    def __init__(self, val):
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
    def read_buffer(cls, buf, offset, cnt=0):
        dbg("reading vector of sz {}".format(cnt))
        v = []
        for _ in range(cnt):
            t = cls.T.read(buf, offset=offset)
            dbg("read {} at offset {}".format(t, offset))
            v.append(t)
            offset += cls.T.sz
        return cls(v)

    def write(self, buf, offset):
        dbg("writing vector ({}) of sz {} at offset {}".format(
            self.T.__name__, self.count(), offset))
        buf[offset: offset +
            self.sz] = struct.pack(self.fmt, len(buf), self.count())
        self.extend_buffer(buf)

    def extend_buffer(self, buf):
        offset = len(buf)
        buf += bytearray(self.count() * self.T.sz)

        for x in self.val:
            dbg("writing  {} at offset {}".format(x, offset))
            x.write(buf, offset)
            offset += self.T.sz

    def plain(self):
        return [i.plain() for i in self.val]


def Vec(T):
    if issubclass(T, ExonumField):
        return type("Vec<{}>".format(T.__name__),
                    (Vector, ),
                    {"T": T})
    raise NotSupported()


class ExonumBase(ExonumSegment):
    def count(self):
        return 1

    def __init__(self, val=None, **kwargs):
        for field in self.__exonum_fields__:
            cls = getattr(self.__class__, field)
            if isinstance(kwargs[field], cls):
                setattr(self, field,  kwargs[field])
            else:
                setattr(self, field,  cls(kwargs[field]))

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            raise CantComare(self.__class__, other.__class__)
        for field in self.__exonum_fields__:
            if getattr(self, field) != getattr(other, field):
                return False
        return True

    def extend_buffer(self, buf):
        offset = len(buf)
        buf += bytearray(self.fields_sz)
        for field in self.__exonum_fields__:
            field = getattr(self, field)
            field.write(buf, offset)
            offset += field.sz

    def __str__(self):
        repr = []
        for field in self.__exonum_fields__:
            repr.append("{} = {}".format(field, getattr(self, field)))
        return "{} ({})".format(self.__class__.__name__, ", ".join(repr))

    @classmethod
    def read_buffer(cls, bytestring, offset=0, sz=1):
        dbg("read_buffer of ExonumBase sz {}".format(sz))
        data = {}
        for field in cls.__exonum_fields__:
            fcls = getattr(cls, field)
            dbg("trying to read {} {} at offset {}".format(field, fcls, offset))
            val = fcls.read(bytestring, offset)
            offset += fcls.sz

            data[field] = val
        return cls(**data)

    def to_bytes(self):
        b = bytearray(0)
        self.extend_buffer(b)
        return bytes(b)

    def plain(self):
        return {
            k: getattr(self, k).plain()
            for k in self.__exonum_fields__
        }


class EncodingStruct(type):
    def __new__(self, name, bases, classdict):
        e_bases = [c for c in bases if issubclass(c, ExonumBase)]
        fields = list(chain(*(c.__exonum_fields__ for c in e_bases)))
        sz = sum(c.sz for c in e_bases)

        for k, v in classdict.items():
            if isinstance(v, type) and issubclass(v, ExonumField):
                fields.append(k)
                sz += v.sz

        classdict['__exonum_fields__'] = fields
        classdict['fields_sz'] = sz

        if not any(issubclass(c, ExonumBase) for c in bases):
            return type(name, (ExonumBase, *bases), classdict)
        else:
            return type(name,  bases, classdict)


if sys.version_info.major < 3 or \
   (sys.version_info.major == 3 and sys.version_info.minor < 6):
    # https://www.python.org/dev/peps/pep-0520/
    from collections import OrderedDict
    EncodingStruct.__prepare__ = classmethod(lambda *_: OrderedDict())
