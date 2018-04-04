from typing import NamedTuple, Type, TypeVar


T = TypeVar('T')


class Key(NamedTuple):
    dependency_type: Type[T]
    name: str = None
