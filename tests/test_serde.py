from exonum.datatypes import *
from exonum.serde import *


def test_simple():
    class X(metaclass=ExonumMeta):
        first = u8
        second = u8
        third = i64

    x1 = X(first = 1, second = 2, third = -658979879)
    b = x1.to_bytes()
    x2 = X.read(b)

    assert x1.first == x2.first
    assert x1.second == x2.second
    assert x1.third == x2.third

def test_simple_string():
    class X(metaclass=ExonumMeta):
        first = Str
        second = u8
        third = i64
        fourth = Str

    x1 = X(first = "Это строка",
           second = 2,
           third = -658979879,
           fourth="یہ بھی ایک تار ہے")

    b = x1.to_bytes()
    x2 = X.read(b)

    print(x1)
    assert x1.first == x2.first
    assert x1.second == x2.second
    assert x1.third == x2.third
    assert x1.fourth == x2.fourth

def test_vec():
    class X(metaclass=ExonumMeta):
        first = Vec(u16)
        second = Vec(Str)

    x1 = X(first = [1,2,3,4,5],
           second = ["Foo", "boo", "фывапролдж!"])
    b = x1.to_bytes()
    x2 = X.read(b)

    assert x1.first == x2.first
    assert x1.second == x2.second
