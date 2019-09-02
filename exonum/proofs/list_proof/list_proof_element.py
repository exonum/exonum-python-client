from typing import NewType, Tuple, Any, Any
import collections

ListProofElementType = Tuple[Any, Any]


class ListProofElement:
    Left = collections.namedtuple('Left', ['left', 'right'])
    Right = collections.namedtuple('Right', ['left', 'right'])
    Full = collections.namedtuple('Full', ['left', 'right'])
    Leaf = collections.namedtuple('Leaf', ['val', 'val_raw'])
    Absent = collections.namedtuple('Absent', ['length', 'hash'])
