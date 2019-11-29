"""Common Utils for Proofs Modules."""
from typing import Any, Dict, Callable, Optional
from logging import getLogger
import re

# Those utils are internal and very simple, so they don't require docs.
# pylint: disable=missing-docstring
# pylint: disable=C0103
logger = getLogger(__name__)


def is_dict(json: Any) -> bool:
    return isinstance(json, dict)


def is_field_dict(json: Dict[Any, Any], field: str) -> bool:
    return isinstance(json.get(field), dict)


def is_field_hash(json: Dict[Any, Any], field: str) -> bool:
    field_value = json.get(field)
    return isinstance(field_value, str) and bool(re.match(r"^[0-9A-Fa-f]{64}$", field_value))


def is_field_hash_or_none(json: Dict[Any, Any], field: str) -> bool:
    return not json.get(field) or is_field_hash(json, field)


def is_field_int(json: Dict[Any, Any], field: str) -> bool:
    return isinstance(json.get(field), int)


def is_field_convertible(json: Dict[Any, Any], field: str, value_to_bytes: Callable[[Any], bytes]) -> bool:
    try:
        if not json.get(field):
            return False
        value_to_bytes(json[field])
        return True
    except ValueError:
        logger.warning("Field '%s' is not convertible.", field)
        return False


def to_bytes(hex_data: str) -> Optional[bytes]:
    if not hex_data:
        return None

    return bytes.fromhex(hex_data)


def calculate_height(number: int) -> int:
    if number < 0:
        logger.warning("Number %s is used for tree height calculation and cannot be less than zero.", number)
        raise ValueError(f"Number {number} is less than zero.")
    if number == 0:
        return 1

    # Height of the tree is the amount of bits in the number that represents
    # the next power of two for the given number.
    # The next power of two is calculated as 1 << (number - 1).bit_length().
    # Thus, (number - 1).bit_length() + 1 is the required amount of bits.
    trailing_zeroes_amount = (number - 1).bit_length()

    return trailing_zeroes_amount + 1


def div_ceil(dividend: int, divider: int) -> int:
    return (dividend + divider - 1) // divider


def reset_bits(value: int, pos: int) -> int:
    """ Resets bits higher than the given pos. """
    reset_bits_mask = ~(255 << pos)
    value &= reset_bits_mask
    return value


def leb128_encode_unsigned(value: int) -> bytes:
    """ Encodes an unsigned number with leb128 algorithm. """
    if value < 0:
        logger.warning("Value passed to LEB128 for unsigned integers should be non-negative.")
        raise ValueError("Value should be non-negative")

    result = []
    while True:
        # Lower 7 bits of value:
        byte = value & 0x7F
        value >>= 7

        if value != 0:  # More bytes to come.
            byte |= 0x80  # Set high order bit.

        result.append(byte)

        if value == 0:
            break

    return bytes(result)
