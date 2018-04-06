from typing import NamedTuple


class Key(NamedTuple):
    dependency_type: type
    name: str
