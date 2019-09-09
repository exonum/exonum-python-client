import re


def is_dict(json):
    return isinstance(json, dict)


def is_field_dict(json, field):
    return isinstance(json.get(field), dict)


def is_field_hash(json, field):
    field = json.get(field)
    return isinstance(field, str) and re.match(r"^[0-9A-Fa-f]{64}$", field)


def is_field_hash_or_none(json, field):
    return not json.get(field) or is_field_hash(json, field)


def is_field_int(json, field):
    return isinstance(json.get(field), int)


def is_field_convertible(json, field, value_to_bytes):
    try:
        if not json.get(field):
            return False
        value_to_bytes(json[field])
        return True
    except ValueError:
        return False


def to_bytes(hex_data):
    if not hex_data:
        return None

    return bytes.fromhex(hex_data)


def calculate_height(number):
    if number < 0:
        raise ValueError("Number {} is less than zero".format(number))
    elif number == 0:
        return 1
    else:
        # Amount of trailing zeroes for the next power of two
        # This works because we can calculate the next power of two as 1 << (number - 1).bit_length()
        # So, (number - 1).bit_length() is the shift => there will be that amount of trailing zeroes in number.
        trailing_zeroes_amount = (number - 1).bit_length()

        return trailing_zeroes_amount + 1


def div_ceil(a, b):
    return (a + b - 1) // b


def reset_bits(value, pos):
    """ Resets bits higher than the given pos. """
    reset_bits_mask = ~(255 << pos)
    value &= reset_bits_mask
    return value


def leb128_encode_unsigned(value: int) -> bytes:
    """ Encodes an unsigned number with leb128 algorithm. """
    if value < 0:
        raise ValueError("Value should be non-negative")

    result = []
    while True:
        # Lower 7 bits of value.
        byte = value & 0x7F
        value >>= 7

        if value != 0:  # More bytes to come.
            byte |= 0x80  # Set high order bit.

        result.append(byte)

        if value == 0:
            break

    return bytes(result)
