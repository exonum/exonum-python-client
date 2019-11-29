""" ProofListKey Module. """
from typing import Dict, Any
from functools import total_ordering
from logging import getLogger

from ..utils import is_field_int
from .errors import MalformedListProofError

# pylint: disable=C0103
logger = getLogger(__name__)


@total_ordering
class ProofListKey:
    """ A structure that represents a key in the list proof. """

    def __init__(self, height: int, index: int):
        self.height = height
        self.index = index

    @classmethod
    def parse(cls, data: Dict[Any, Any]) -> "ProofListKey":
        """ Parses ProofListKey from dict. """
        if not is_field_int(data, "index") or not is_field_int(data, "height"):
            err = MalformedListProofError.parse_error(str(data))
            logger.warning(str(err))
            raise err

        return cls(data["height"], data["index"])

    def is_left(self) -> bool:
        """ Returns true if this key is in the left branch of the proof. """
        return self.index % 2 == 0

    def parent(self) -> "ProofListKey":
        """ Returns the parent key for this key. """
        return ProofListKey(self.height + 1, self.index >> 1)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProofListKey):
            raise TypeError("Attempt to compare ProofListKey with an object of a different type.")
        return self.index == other.index and self.height == other.height

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ProofListKey):
            raise TypeError("Attempt to compare ProofListKey with an object of a different type.")

        # Try to compare by height, otherwise compare by index.
        if self.height != other.height:
            return self.height < other.height

        return self.index < other.index
