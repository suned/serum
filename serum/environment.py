from functools import wraps
from typing import Type, TypeVar, Set
from .exceptions import (
    InvalidDependency,
    NoEnvironment,
    UnregisteredDependency,
)
from .component import Component
import threading
import inspect

C = TypeVar('C', bound=Component)


class _LocalStorage(threading.local):
    def __init__(self):
        self.current_env: Environment = None


class Environment:
    __local_storage = _LocalStorage()

    @staticmethod
    def _current_env() -> 'Environment':
        return Environment.__local_storage.current_env

    @staticmethod
    def _set_current_env(env: 'Environment'):
        Environment.__local_storage.current_env = env

    def __init__(self, *args: Type[C]) -> None:
        self.__registry: Set = set()
        self.__is_active = False
        self.__old_current = None
        for c in args:
            self.__use(c)

    def __use(self, component: Type[C]):
        if self.__is_active:
            raise ValueError('Can\'t change active environment')
        if not issubclass(component, Component):
            raise InvalidDependency(
                'Attempt to register type that is not a Component: {}'.format(
                    str(component)
                )
            )
        self.__registry.add(component)
        return self

    def __contains__(self, component: Type[C]):
        return component in self.__registry

    def __call__(self, f):
        @wraps(f)
        def run_in(*args, **kwargs):
            with self:
                f(*args, **kwargs)
        return run_in

    def __iter__(self):
        return iter(self.__registry)

    def __or__(self, other: 'Environment') -> 'Environment':
        new_registry = self.__registry | other.__registry
        return Environment(*new_registry)

    def __enter__(self):
        self.__is_active = True
        self.__old_current = Environment._current_env()
        Environment._set_current_env(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__is_active = False
        Environment._set_current_env(self.__old_current)
        self.__old_current = None

    @staticmethod
    def get(component: Type[C]) -> C:
        if Environment._current_env() is None:
            raise NoEnvironment(
                'Can\'t inject components outside an environment'
            )
        try:
            subtype = Environment._find_subtype(component)
            return subtype()
        except UnregisteredDependency:
            try:
                return component()
            except TypeError:
                raise UnregisteredDependency(
                    'No concrete implementation of {} found'.format(
                        str(component)
                    )
                )

    @staticmethod
    def _find_subtype(component: Type[C]) -> Type[C]:
        def mro_distance(subtype: Type[C]) -> int:
            mro = inspect.getmro(subtype)
            return mro.index(component)

        subtypes = [c for c in Environment._current_env()
                    if issubclass(c, component)]
        if not subtypes:
            raise UnregisteredDependency(
                'Unregistered dependency: {}'.format(str(component))
            )
        return max(subtypes, key=mro_distance)


__all__ = ['Environment']
