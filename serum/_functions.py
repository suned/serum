from typing import TypeVar, Type, cast
from unittest.mock import MagicMock

from .exceptions import InvalidDependency, CircularDependency
from ._component import Component
from ._environment import Environment

C = TypeVar('C', bound=Component)
T = TypeVar('T')


def inject(component: Type[C]) -> C:
    """
    Inject a Component of type component here
    :param component: The type to inject
    :return: A lazily instantiated component
    """
    if not issubclass(component, Component):
        raise InvalidDependency(
            'Attempt to inject type that is not a Component: {}'.format(
                str(component)
            )
        )

    def get_instance(caller):
        return Environment.provide(component, caller)

    return cast(C, property(fget=get_instance))


def immutable(value: T) -> T:
    """
    Add a static constant to a class.
    :param value: The value to add
    :return: property that returns value
    """
    def get(_) -> T:
        return value
    return cast(T, property(fget=get))


def mock(component: Type[C]) -> MagicMock:
    """
    Mock a component in the current environment
    :param component: The type to mock
    :return: unittest.mock.MagicMock instance that replaces component in this
             environment
    """
    return Environment.mock(component)


__all__ = ['inject', 'immutable', 'mock']
