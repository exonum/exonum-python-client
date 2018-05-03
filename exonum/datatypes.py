import ipaddress
import struct

from datetime import datetime
from uuid import UUID

import nanotime

from .util import make_class_ordered
from . import ExonumException


class NotImplementedYet(ExonumException):
    pass

class UnsupportedDatatype(ExonumException):
    pass


class NotSupported(ExonumException):
    pass


class CantComare(ExonumException):
    pass


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

    def write(self, buf, pos):
        raw = struct.pack(self.fmt, self.val)
        buf[pos: pos + self.sz] = raw

    def to_bytes(self):
        b = bytearray(self.sz)
        self.write(b, 0)
        return bytes(b)

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.val)

    def plain(self):
        self.val

class ExonumSegment(ExonumField):
    sz = 8
    fmt = "<2I"
    T = None

    def write(self, buf, pos):
        buf[pos: pos + self.sz] = struct.pack(self.fmt, len(buf), self.count())
        self.extend_buffer(buf)

    @classmethod
    def read(cls, buf, offset=0):
        pos, cnt = struct.unpack_from(cls.fmt, buf, offset=offset)
        return cls(cls.read_data(buf, pos, cnt))


class boolean(ExonumField):
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
        else:
            raise UnsupportedDatatype(
                "Type {} is not supported for initializing DateTime"
                .format(type(val)))

    def write(self, buf, pos):
        sec = int(self.val.seconds())
        nan = (self.val - nanotime.seconds(sec)).nanoseconds()
        raw = struct.pack(self.fmt, sec, nan)
        buf[pos: pos + self.sz] = raw

    @classmethod
    def read(cls, buf, offset=0):
        sec, nan = struct.unpack_from(cls.fmt, buf, offset=offset)
        return cls(nanotime.seconds(sec) + nanotime.nanoseconds(nan))

    def plain(self):
        raise NotImplementedYet(self.__class__)


class Uuid(ExonumField):
    sz = 16
    fmt = "<16B"

    def __init__(self, val):
        if isinstance(val, UUID):
            self.val = val
        else:
            self.val = UUID(val)

    def write(self, buf, pos):
        buf[pos: pos + self.sz] = self.val.bytes

    @classmethod
    def read(cls, buf, offset=0):
        data, = struct.unpack_from(cls.fmt, buf, offset=offset)
        return cls(UUID(bytes=data))

    def plain(self):
        return self.val.hex


class SocketAddr(ExonumField):
    sz = 6
    fmt = "<4BH"

    def __init__(self, val):
        ip = ipaddress.IPv4Address(val[0])
        self.val = (ip, val[1])

    def write(self, buf, pos):
        raw = self.val[0].packed + struct.pack("<H", self.val[1])
        buf[pos: pos + self.sz] = raw

    @classmethod
    def read(cls, buf, offset=0):
        data = struct.unpack_from(cls.fmt, buf, offset=offset)
        return cls(data)

    def plain(self):
        raise NotImplementedYet(self.__class__)


class Str(ExonumSegment):
    def count(self):
        return len(self.val.encode())

    def extend_buffer(self, buf):
        buf += self.val.encode()

    @staticmethod
    def read_data(buf, pos, cnt):
        return buf[pos: pos + cnt].decode("utf-8")

    def plain(self):
        return self.val


class VecSimple(ExonumSegment):
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
    def read_data(cls, buf, pos, cnt):
        v = []
        for _ in range(cnt):
            t = cls.T.read(buf, offset=pos)
            v.append(t)
            pos += cls.T.sz
        return v

    def write(self, buf, pos):
        buf[pos: pos + self.sz] = struct.pack(self.fmt, len(buf), self.count())
        self.extend_buffer(buf)

    def extend_buffer(self, buf):
        data = bytearray(self.count() * self.T.sz)
        offset = 0
        for x in self.val:
            x.write(data, offset)
            offset += self.T.sz
        buf += data

    def plain(self):
        return [i.plain() for i in self.val]


class VecFields(VecSimple):
    @classmethod
    def read_data(cls, buf, pos, cnt):
        v = []
        for n in range(cnt):
            offset, _ = struct.unpack_from(cls.fmt, buf, offset=pos)
            t = cls.T.read(buf, offset=offset)
            v.append(t)
            pos += ExonumSegment.sz
        return v

    def extend_buffer(self, buf):
        pointers_sz = self.count() * 8  # FIXME
        data_sz = self.count() * self.T.sz
        start = len(buf)
        data_start = start + pointers_sz
        buf += bytearray(pointers_sz + data_sz)

        for el in self.val:
            pointer = struct.pack(self.fmt, data_start, self.T.sz)
            buf[start: start + self.sz] = pointer
            el.write(buf, pos=data_start)
            data_start += self.T.sz
            start += 8


def Vec(T):
    if issubclass(T, ExonumBase):
        return type("Vec<{}>".format(T.__name__),
                    (VecFields, ),
                    {"T": T})

    if issubclass(T, ExonumSegment):
        raise NotSupported()

    if issubclass(T, ExonumField):
        return type("Vec<{}>".format(T.__name__),
                    (VecSimple, ),
                    {"T": T})


class ExonumBase(ExonumField):
    def __init__(self, **kwargs):
        for field in self.__exonum_fields__:
            cls = getattr(self.__class__, field)
            if isinstance(kwargs[field], cls):
                setattr(self, field,  kwargs[field])
            else:
                setattr(self, field,  cls(kwargs[field]))

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            raise CantComare()
        for field in self.__exonum_fields__:
            if getattr(self, field) != getattr(other, field):
                return False
        return True

    def write(self, buf, pos):
        for field in self.__exonum_fields__:
            field = getattr(self, field)
            field.write(buf, pos)
            pos += field.sz

    def __str__(self):
        repr = []
        for field in self.__exonum_fields__:
            repr.append("{} = {}".format(field, getattr(self, field)))
        return "{} ({})".format(self.__class__.__name__, ", ".join(repr))

    @classmethod
    def read(cls, bytestring, offset=0):
        data = {}
        for field in cls.__exonum_fields__:
            fcls = getattr(cls, field)
            val = fcls.read(bytestring, offset)
            offset += fcls.sz
            data[field] = val
        return cls(**data)

    def plain(self):
        return {
            k: getattr(self, k).plain()
            for k in self.__exonum_fields__
        }

class EncodingStruct(type):
    def __new__(self, name, bases, classdict):
        fields = []
        sz = 0
        for k, v in classdict.items():
            if isinstance(v, type) and issubclass(v, ExonumField):
                fields.append(k)
                sz += v.sz

        classdict['__exonum_fields__'] = fields
        classdict['sz'] = sz

        return type(name, (ExonumBase, *bases), classdict)


make_class_ordered(EncodingStruct)
