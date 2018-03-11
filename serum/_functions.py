from typing import TypeVar, Type, cast, overload, Any, Union
from unittest.mock import MagicMock

import os

from serum._lazy_dependency import LazyDependency
from ._environment import provide
from .exceptions import InvalidDependency, UnknownEnvironment, NoEnvironment
from ._component import Component
from ._environment import Environment

C = TypeVar('C', bound=Component)
T = TypeVar('T')


class Key:
    pass


@overload
def inject(dependency: Type[C]) -> C:
    pass  # pragma: no cover


@overload
def inject(dependency: str) -> Any:
    pass  # pragma: no cover


def inject(dependency):
    """
    Inject a dependency
    :param dependency: The Component type or key to inject
    :return: Instantiated Component or key
    """
    if not (isinstance(dependency, str) or issubclass(dependency, Component)):
        raise InvalidDependency(
            'Attempt to inject dependency that is not a Component or str: {}'.format(
                str(dependency)
            )
        )

    try:
        return provide(dependency, Key())
    except NoEnvironment:
        return LazyDependency(dependency)


def immutable(value: T) -> T:
    """
    Add a static constant to a class.
    :param value: The value to add
    :return: property that returns value
    """
    return cast(T, property(fget=lambda _: value))


def mock(dependency: Union[str, Type[C]]) -> MagicMock:
    """
    Mock a component in the current environment
    :param dependency: The type to mock
    :return: unittest.mock.MagicMock instance that replaces component in this
             environment
    """
    return Environment.mock(dependency)


def match(environment_variable: str,
          default: Environment = None,
          **environments) -> Environment:
    """
    Match environment variable with Environment
    :param environment_variable: environment variable to match environment against
    :param default: default environment when no value is
                    assigned to environment_variable
    :param environments: kwargs of environments to use for different values of
                         environment_variable
    :return: Environment matched against the value of environment_variable
             or default Environment is no value is assigned
    """
    environment = os.environ.get(environment_variable, 'default')
    if environment == 'default':
        if default is None:
            raise UnknownEnvironment(
                'No environment specified and no default environment'
            )
        return default
    try:
        return environments[environment]
    except KeyError:
        raise UnknownEnvironment(environment)


__all__ = ['inject', 'immutable', 'mock', 'match']
