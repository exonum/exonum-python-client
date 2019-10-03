"""Internal representation of the List Proof element."""
from typing import Tuple, Any
import collections

ListProofElementType = Tuple[Any, Any]


class ListProofElement:
    """Internal representation of the List Proof element."""

    Left = collections.namedtuple("Left", ["left", "right"])
    Right = collections.namedtuple("Right", ["left", "right"])
    Full = collections.namedtuple("Full", ["left", "right"])
    Leaf = collections.namedtuple("Leaf", ["val", "val_raw"])
    Absent = collections.namedtuple("Absent", ["length", "hash"])
