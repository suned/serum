from typing import NamedTuple, Type, Union, TypeVar

from serum._key import Key


T = TypeVar('T')


class DependencyConfiguration(NamedTuple):
    dependency: Union[Key, Type[T]]
    name: str
    owner: object
