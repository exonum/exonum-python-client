from typing import Optional, Any, Dict

from .errors import MalformedMapProofError


class OptionalEntry:
    def __init__(self, key: Any, value: Optional[Any]):
        self.key = key
        self.value = value
        self.is_missing = False if value else True

    def __repr__(self) -> str:
        if self.is_missing:
            return 'Missing [key: {}]'.format(self.key)
        else:
            return 'Entry [key: {}, value: {}]'.format(self.key, self.value)

    @staticmethod
    def parse(data: Dict[str, Any]) -> 'OptionalEntry':
        if data.get('missing'):
            return OptionalEntry(key=data['missing'], value=None)
        elif data.get('key') and data.get('value'):
            return OptionalEntry(key=data['key'], value=data['value'])
        else:
            raise MalformedMapProofError.malformed_entry(data)
