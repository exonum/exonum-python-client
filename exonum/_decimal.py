# coding: utf-8
import decimal

from .error import DecimalOverflow, NotImplementedYet

SCALE_MASK = 0x00FF0000
SIGN_MASK = 0x80000000
U32_MASK = 0xFFFFFFFF
SCALE_SHIFT = 16
MAX_PRECISION = 28

ctx = decimal.getcontext()
ctx.prec = MAX_PRECISION + 1
ctx.Emax = MAX_PRECISION
ctx.Emin = -MAX_PRECISION


# Bits 0-15: unused
#   Bits 16-23: Contains "e", a value between 0-28 that indicates the scale
#   Bits 24-30: unused
#   Bit 31: the sign of the Decimal value, 0 meaning positive and
#   1 meaning negative.

#   flags: u32,
#   The lo, mid, hi, and flags fields contain the representation of the
#   Decimal value as a 96-bit integer.
#   hi: u32,
#   lo: u32,
#   mid: u32,


def mul_part(left, right, high):
    res = left * right + high
    hi = (res >> 32) & U32_MASK
    lo = res & U32_MASK
    return (lo, hi)


def _mul(bits, m):
    overflow = 0
    for idx, b in enumerate(bits):
        lo, hi = mul_part(b, m, overflow)
        bits[idx] = lo
        overflow = hi
    if overflow > 0:
        raise DecimalOverflow()


def _add(value, by):
    to_add = by
    for i in range(len(value)):
        sum = value[i] + by
        value[i] = sum & U32_MASK
        to_add = sum >> 32
        if to_add == 0:
            break
    else:
        raise DecimalOverflow()


def _div(bits, divisor):
    if divisor == 0:
        raise ZeroDivisionError()

    elif divisor == 1:
        return 0
    else:
        remainder = 0
        for idx, b in reversed(list(enumerate(bits))):
            temp = (remainder << 32) + b
            remainder = temp % divisor
            bits[idx] = temp // divisor
    return remainder


def scale(flags):
    return (flags & SCALE_MASK) >> SCALE_SHIFT


def is_negative(flags):
    return flags & SIGN_MASK > 0


def to_bytes(d):
    dt = d.as_tuple()
    if dt.exponent > 0:
        raise NotImplementedYet("Positive exp in decimal ")

    digits = dt.digits

    data = [0, 0, 0]

    for digit in digits:
        _mul(data, 10)
        _add(data, digit)

    flags = abs(dt.exponent) << SCALE_SHIFT

    if dt.sign:
        flags |= SIGN_MASK

    # py2 compat
    data.insert(0, flags)
    return data


def from_bytes(flags, *data):
    data = list(data)
    digits = []
    while not all(x == 0 for x in data):
        remainder = _div(data, 10)
        digits.append(remainder)
    digits.reverse()
    sign = is_negative(flags)
    exponent = scale(flags) * -1
    dt = decimal.DecimalTuple(sign, digits, exponent)
    return decimal.Decimal(dt)
