from typing import TypeVar, Type, cast, Any
from .exceptions import InvalidDependency
from .component import Component
from .environment import Environment

C = TypeVar('C', bound=Component)
T = TypeVar('T')


def inject(component: Type[C]) -> C:
    if not issubclass(component, Component):
        raise InvalidDependency(
            'Attempt to inject type that is not a Component: {}'.format(
                str(component)
            )
        )

    def get(_) -> C:
        return Environment.get(component)
    return cast(C, property(fget=get))


def immutable(value: T) -> T:
    def get(_) -> T:
        return value
    return cast(T, property(fget=get))


__all__ = ['inject', 'immutable']
