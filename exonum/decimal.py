import decimal
import struct

from .error import DecimalOverflow, NotImplementedYet

SIGN_MASK = 0x8000_0000
U32_MASK = 0xFFFF_FFFF
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


# def add_internal(value, by):
#     carry = 0
#     vl = len(value)
#     bl = len(by)

#     if vl >= bl:
#         for i in range(bl):
#             sum = value[i] + by[i] + carry
#             value[i] = (sum & U32_MASK)
#             carry = sum >> 32

#         if vl > bl and carry > 0:
#             for idx in range(bl, vl):
#                 sum = value[idx] + carry
#                 value[idx] = sum & U32_MASK
#                 carry = sum >> 32

#     elif vl + 1 == bl:
#         for i in range(vl):
#             sum = value[i] + by[i] + carry
#             value[i] = (sum & U32_MASK)
#             carry = sum >> 32
#         carry += by[vl]

#     else:
#         raise DecimalInternalError(
#             "Internal error: "
#             "add using incompatible length arrays. {} {}".format(vl, bl))

#     return carry

def _add(value, by):
    to_add = by
    for i in range(len(value)):
        sum = value[i] + by
        value[i] = (sum & U32_MASK)
        to_add = sum >> 32
        if to_add == 0:
            break
    else:
        raise DecimalOverflow()


def to_bytes(d):
    dt = d.as_tuple()
    if dt.exponent > 0:
        raise NotImplementedYet("Positive exp in decimal ")

    digits = dt.digits

    data = [0,0,0]

    for digit in digits:
        _mul(data, 10)
        _add(data, digit)

    flags = dt.exponent << SCALE_SHIFT

    if dt.sign:
        flags |= SIGN_MASK

    return (flags, *data)
