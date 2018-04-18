import struct
import sys

from types import FunctionType
from collections import OrderedDict

# do we need this at all?

SIGNATURE_LEN = 64  # bytes
SERVICE_DATA_LEN = 10  # bytes

class ExonumField:
    fmt = None

    @classmethod
    def read(self, buf, offset):
        return struct.unpack_from(self.fmt, buf, offset=offset)

    @classmethod
    def write(self, val):
        print(self.fmt, val, struct.pack(self.fmt, val))
        return struct.pack(self.fmt, val)


class Exonum:
    class boolean(ExonumField):
        fmt = '<B'

    class u8(ExonumField):
        fmt = '<B'

    class u16(ExonumField):
        fmt = '<H'

    class u32(ExonumField):
        fmt = '<I'

    class u64(ExonumField):
        fmt = '<L'

    class i8(ExonumField):
        fmt = '<b'

    class i16(ExonumField):
        fmt = '<h'

    class i32(ExonumField):
        fmt = '<i'

    class i64(ExonumField):
        fmt = '<l'

    class vec(ExonumField):
        pass

    class str(ExonumField):
        pass

    class ip4addr(ExonumField):
        pass


def fields__init__(self, **kwargs):
    for field in self.__exonum_fields__:
        setattr(self, field, kwargs[field])

def binary(self):
    b = []
    for field in self.__exonum_fields__:
        cls = getattr(self.__class__, field)
        b.append(cls.write(getattr(self, field)))
    return b''.join(b)

class ExonumMeta(type):
    _exclude = set(dir(type))
    def __new__(self, name, bases, classdict):
        fields = [k for k, v in classdict.items()
                  if k not in self._exclude
                  and not isinstance(v, (FunctionType, classmethod, staticmethod))]
        classdict['__exonum_fields__'] = fields
        cls = type.__new__(self, name, bases, classdict)
        cls.__init__ = fields__init__
        cls.binary = binary
        return cls

# https://www.python.org/dev/peps/pep-0520/
if sys.version_info.major < 3 or \
       (sys.version_info.major == 3 and sys.version_info.minor < 6):
    ExonumMeta.__prepare__  = classmethod(lambda *_: OrderedDict())


class Fuck(metaclass = ExonumMeta):
    first = Exonum.u8
    second = Exonum.u32
