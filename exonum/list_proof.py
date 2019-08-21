import collections

from .errors import MalformedProofError


def is_dict(json):
    return isinstance(json, dict)


def is_field_dict(json, field):
    return isinstance(json.get(field), dict)


def is_field_hash(json, field):
    try:
        field = json.get(field)
        return isinstance(field, str) and len(field) == 64 and int(field, 16)
    except ValueError:
        return False


def is_field_hash_or_none(json, field):
    return not json.get(field) or is_field_hash(json, field)


def is_field_int(json, field):
    return isinstance(json.get(field), int)


class ProofParser:
    @staticmethod
    def parse(json):
        if is_dict(json):
            for kind, condition in ListProof.NODE_CONDITIONS.items():
                if condition(json):
                    return ListProof.NODE_FACTORY[kind](json)

        raise MalformedProofError('Received malformed proof: {}'.format(json))


class ListProof:
    Left = collections.namedtuple('Left', ['left', 'right'])
    Right = collections.namedtuple('Right', ['left', 'right'])
    Full = collections.namedtuple('Full', ['left', 'right'])
    Leaf = collections.namedtuple('Leaf', ['val'])
    Absent = collections.namedtuple('Absent', ['length', 'hash'])

    NODE_CONDITIONS = {
        'Left': lambda json: is_field_dict(json, 'left') and is_field_hash_or_none(json, 'right'),
        'Right': lambda json: is_field_hash(json, 'left') and is_field_dict(json, 'right'),
        'Full': lambda json: is_field_dict(json, 'left') and is_field_dict(json, 'right'),
        'Leaf': lambda json: is_field_hash(json, 'val'),
        'Absent': lambda json: is_field_int(json, 'length') and is_field_hash(json, 'hash'),
    }

    NODE_FACTORY = {
        'Left': lambda json: ListProof.Left(ProofParser.parse(json['left']), json.get('right')),
        'Right': lambda json: ListProof.Right(json['left'], ProofParser.parse(json['right'])),
        'Full': lambda json: ListProof.Full(ProofParser.parse(json['left']), ProofParser.parse(json['right'])),
        'Leaf': lambda json: ListProof.Leaf(json['val']),
        'Absent': lambda json: ListProof.Absent(json['length'], json['hash']),
    }

    def __init__(self, proof_json):
        self._proof = ProofParser.parse(proof_json)

    def validate(self, length, expected_hash):
        pass
