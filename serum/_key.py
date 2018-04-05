from typing import NamedTuple, Type, TypeVar


class Key(NamedTuple):
    dependency_type: type
    name: str = None
