from typing import TypeVar, Union


class NamedDependency:
    pass


T = TypeVar('T')
Name = Union[NamedDependency, T]


def get_dependency_type(named_dependency) -> type:
    try:
        return next(a for a in named_dependency.__args__
                    if a not in (NamedDependency, T))
    except StopIteration:
        return object


def is_named_dependency(dependency) -> bool:
    is_union = str(type(dependency)) == 'typing.Union'
    name = f'{__name__}.{NamedDependency.__name__}'
    return is_union and name in str(dependency)


__all__ = ['Name', 'NamedDependency']
