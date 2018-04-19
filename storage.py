import ipaddress
import struct
import sys

from collections import OrderedDict
from datetime import datetime
from types import FunctionType
from uuid import UUID

import nanotime


class ExonumField:
    sz = 1
    fmt = None

    def __init__(self, val):
        self.val = val

    @classmethod
    def read(cls, buf, offset):
        val, =  struct.unpack_from(cls.fmt, buf, offset=offset)
        return cls(val)

    def write(self, buf, pos):
        raw = struct.pack(self.fmt, self.val)
        buf[pos: pos + self.sz] = raw

    def __str__(self):
        return "{} {}".format(self.__class__, self.val)


class ExonumSegment(ExonumField):
    sz = 8
    fmt = "<2I"
    T = None
    item_size = 1

    def write(self, buf, pos):
        buf[pos: pos + self.sz] = struct.pack(self.fmt, len(buf), self.count())
        buf += self.enc()

    @classmethod
    def read(cls, buf, offset):
        pos, cnt = struct.unpack_from(cls.fmt, buf, offset=offset)
        return cls(cls.read_data(buf, pos, cnt))


class Exonum:
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

    class UnsupportedDatatype(Exception):
        pass

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
                raise Exonum.UnsupportedDatatype(
                    "Type {} is not supported for initializing DateTime"
                    .format(type(val)))

        def write(self, buf, pos):
            sec = int(self.val.seconds())
            nan = (self.val - nanotime.seconds(sec)).nanoseconds()
            raw = struct.pack(self.fmt, sec, nan)
            buf[pos: pos + self.sz] = raw

        @classmethod
        def read(cls, buf, offset):
            sec, nan = struct.unpack_from(cls.fmt, buf, offset=offset)
            return cls(nanotime.seconds(sec) + nanotime.nanoseconds(nan))

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
        def read(cls, buf, offset):
            data, = struct.unpack_from(cls.fmt, buf, offset=offset)
            return cls(UUID(bytes=data))

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
        def read(cls, buf, offset):
            data = struct.unpack_from(cls.fmt, buf, offset=offset)
            return cls(data)

    class Str(ExonumSegment):
        def count(self):
            return len(self.val.encode())

        def enc(self):
            return self.val.encode()

        @staticmethod
        def read_data(buf, pos, cnt):
            return buf[pos: pos + cnt].decode("utf-8")

    class VecInternal(ExonumSegment):
        def count(self):
            return len(self.val)

        @classmethod
        def read_data(cls, buf, pos, cnt):
            v = []
            for n in range(cnt):
                offset, _ = struct.unpack_from(cls.fmt, buf, offset=pos)
                t = cls.T.read(buf, offset=offset)
                v.append(t)
                pos += ExonumSegment.sz
            return v

        def __str__(self):
            repr = ["{}".format(i) for i in self.val]
            return "{} ({})".format(self.__class__.__name__, ", ".join(repr))

    @classmethod
    def Vec(cls, T):
        return type("Exonum.Vec<{}>".format(T.__name__),
                    (cls.VecInternal, ),
                    {"T": T, "item_size": T.sz})

    # class Arr(Vec):
    #     pass

class ExonumBase(ExonumField):
    def __init__(self, **kwargs):
        for field in self.__exonum_fields__:
            cls = getattr(self.__class__, field)
            if isinstance(kwargs[field], cls):
                setattr(self, field,  kwargs[field])
            else:
                setattr(self, field,  cls(kwargs[field]))


    def write(self, buf, pos):
        for field in self.__exonum_fields__:
            field = getattr(self, field)
            field.write(buf, pos)
            pos += field.sz

    def __str__(self):
        repr = []
        for field in self.__exonum_fields__:
            cls = getattr(self.__class__, field)
            repr.append("{} = {}({})".format(field, cls.__name__, getattr(self, field).val))
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

_callables = (FunctionType, classmethod, staticmethod)
_exclude = set(dir(type))

class ExonumMeta(type):
    def __new__(self, name, bases, classdict):
        fields = []
        sz = 0
        for k, v in classdict.items():
            if (k not in _exclude and not isinstance(v, _callables)):
                fields.append(k)
                sz += v.sz

        classdict['__exonum_fields__'] = fields
        classdict['sz'] = sz

        return type(name, (ExonumBase, *bases), classdict)


# https://www.python.org/dev/peps/pep-0520/
if sys.version_info.major < 3 or \
       (sys.version_info.major == 3 and sys.version_info.minor < 6):
    ExonumMeta.__prepare__  = classmethod(lambda *_: OrderedDict())



if __name__ == '__main__':
    class TwoIntegers(metaclass=ExonumMeta):
        first = Exonum.u8
        second = Exonum.u8

    class Wow(metaclass=ExonumMeta):
        z = Exonum.Vec(TwoIntegers)

    class WowAdv(metaclass=ExonumMeta):
        z = Exonum.Vec(TwoIntegers)
        j = TwoIntegers

    # with open("two_int.bin", 'rb') as f:
    #     content = f.read()
    #     print(TwoIntegers.read(content))

    # [8, 0, 0, 0,
    #  3, 0, 0, 0,
    # 32, 0, 0, 0,  2, 0, 0, 0,
    # 34, 0, 0, 0,  2, 0, 0, 0,
    # 36, 0, 0, 0,  2, 0, 0, 0,
    # 1,  2,
    # 3,  4,
    # 5,  6]

    with open("wow.bin", 'rb') as f:
        content = f.read()
        w = Wow.read(content)
        print(w.z)

    # with open("wowx.bin", 'wb') as f:
    #     a = Wow(z = ([TwoIntegers(first=1, second=2)]))
    #     b = bytearray(a.sz)
    #     a.write(b, 0)
    #     f.write(a)

    # with open("wow_adv.bin", 'rb') as f:
    #     content = f.read()
    #     w = WowAdv.read(content)
    #     print(w.j.first)
