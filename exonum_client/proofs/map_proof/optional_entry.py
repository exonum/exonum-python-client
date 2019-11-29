"""Module with OptionalEntry of MapProof."""
from typing import Optional, Any, Dict
from logging import getLogger

from .errors import MalformedMapProofError

# pylint: disable=C0103
logger = getLogger(__name__)


class OptionalEntry:
    """Optional entry is an entry of MapProof which can either miss a key or a key/value pair."""

    def __init__(self, key: Any, value: Optional[Any]):
        self.key = key
        self.value = value
        self.is_missing = not value  # False if the value is set.

    def __repr__(self) -> str:
        if self.is_missing:
            return "Missing [key: {}]".format(self.key)

        return "Entry [key: {}, value: {}]".format(self.key, self.value)

    @staticmethod
    def parse(data: Dict[str, Any]) -> "OptionalEntry":
        """Parsed an OptionalEntry from the provided JSON dict."""
        if data.get("missing"):
            return OptionalEntry(key=data["missing"], value=None)

        if data.get("key") and data.get("value"):
            return OptionalEntry(key=data["key"], value=data["value"])

        logger.warning("Failed to parse an OptionalEntry from the provided JSON dict.")
        raise MalformedMapProofError.malformed_entry(data)
