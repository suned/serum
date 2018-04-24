from typing import TypeVar, Type, cast, Union
from unittest.mock import MagicMock

import os
from .exceptions import UnknownEnvironment
from ._context import Context

T = TypeVar('T')


def mock(dependency: Union[str, Type[T]]) -> MagicMock:
    """
    Mock a dependency in the current environment
    :param dependency: The type to mock
    :return: unittest.mock.MagicMock instance that replaces component in this
             environment
    """
    return Context.mock(dependency)


def match(environment_variable: str,
          default: Context = None,
          **environments) -> Context:
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


__all__ = ['mock', 'match']
