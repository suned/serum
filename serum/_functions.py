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

    def generate() -> C:
        import ipdb
        ipdb.sset_trace()
        callers = dict()
        while True:
            caller = yield
            if caller in callers:
                instance = callers[caller]
                yield instance
            else:
                instance = Environment.provide(component)
                callers[caller] = instance
                yield instance

    component_generator = generate()
    next(component_generator)

    def get_instance(caller):
        try:
            instance = component_generator.send(caller)
            next(component_generator)
            return instance
        except ValueError:
            raise CircularDependency(
                'Circular dependency encountered while injecting {} in {}'.format(
                    str(component),
                    str(caller)
                )
            )

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
    return Environment._mock(component)


__all__ = ['inject', 'immutable', 'mock']
