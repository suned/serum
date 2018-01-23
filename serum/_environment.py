from unittest.mock import MagicMock

from functools import wraps
from typing import Type, TypeVar, Set, Union, Dict

from .exceptions import (
    InvalidDependency,
    NoEnvironment,
    UnregisteredDependency,
    AmbiguousDependencies,
    CircularDependency)
from ._component import Component, Singleton
import threading
import inspect
from collections import Counter

C = TypeVar('C', bound=Component)
S = TypeVar('S', bound=Singleton)


class _LocalStorage(threading.local):
    def __init__(self):
        self.current_env: Environment = None


class Environment:
    """
    Context manager/decorator for providing instances of Component:

    with Environment(MyDependency):
        NeedsDependency()
    or

    @Environment(MyDependency):
    def fun():
        NeedsDependency()
    """
    __local_storage = _LocalStorage()

    @staticmethod
    def _current_env() -> 'Environment':
        return Environment.__local_storage.current_env

    @staticmethod
    def _mock(component: Type[C]):
        current_env = Environment._current_env()
        if current_env is None:
            raise NoEnvironment(
                'Can\t register mock outside environment'
            )
        mock = MagicMock()
        current_env.__mocks[component] = mock
        return mock

    @staticmethod
    def _set_current_env(env: 'Environment'):
        Environment.__local_storage.current_env = env

    def __init__(self, *args: Type[C]) -> None:
        """
        Construct a new environment
        :param args: Components to provide in this environment
        """
        self.__registry: Set[Type[C]] = set()
        self.__old_current: Environment = None
        self.__mocks: Dict[Type[C], MagicMock] = dict()
        self.__singletons: Dict[Type[C], S] = dict()
        self.__instances = dict()
        for c in args:
            self.__use(c)

    def __use(self, component: Type[C]):
        if not issubclass(component, Component):
            raise InvalidDependency(
                'Attempt to register type that is not a Component: {}'.format(
                    str(component)
                )
            )
        self.__registry.add(component)
        return self

    def __contains__(self, component: Type[C]):
        """
        Test if a Component is registered in this environment
        :param component: Component to test
        :return: True if component is registered in this environment else False
        """
        return component in self.__registry

    def __call__(self, f):
        """
        Decorate a function to run in this environment
        :param f: function to decorate
        :return: decorated function
        """
        @wraps(f)
        def run_in(*args, **kwargs):
            with self:
                f(*args, **kwargs)
        return run_in

    def __iter__(self):
        """
        Iterate over the components registered in this environment
        :return: Iterator of components
        """
        return iter(self.__registry)

    def __or__(self, other: 'Environment') -> 'Environment':
        """
        Combine this environment with another, such that the new environment
        can provide all components in both environments
        :param other: Environment to combine with this one
        :return: New environment with components from this and the other
                 environment
        """
        new_registry = self.__registry | other.__registry
        return Environment(*new_registry)

    def __enter__(self):
        """
        Register this environment as the current environment in this thread
        :return:
        """
        self.__old_current = Environment._current_env()
        Environment._set_current_env(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        De-register this environment as the current environment in this thread
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self.__mocks = dict()
        Environment._set_current_env(self.__old_current)
        self.__old_current = None

    @staticmethod
    def provide(component: Type[C], caller: object) -> Union[C, MagicMock, S]:
        """
        Provide a component in this environment
        :param caller:
        :param component: The type to provide
        :return: Instance of the most specific subtype of component
                 in this environment
        """
        if Environment._current_env() is None:
            raise NoEnvironment(
                'Can\'t inject components outside an environment'
            )
        current_env = Environment._current_env()

        def singleton(st):
            if st in current_env.__singletons:
                return current_env.__singletons[st]
            else:
                singleton_instance = st()
                current_env.__singletons[st] = singleton_instance
                return singleton_instance

        def instance(st):
            if (component, caller) in current_env.__instances:
                return current_env.__instances[(component, caller)]
            component_instance = st()
            current_env.__instances[(component, caller)] = component_instance
            return component_instance

        def mock():
            return current_env.__mocks[component]

        def is_mocked():
            return component in current_env.__mocks

        def is_singleton(st):
            return issubclass(st, Singleton)

        if is_mocked():
            return mock()
        try:
            try:
                subtype = Environment._find_subtype(component)
                if is_singleton(subtype):
                    return singleton(subtype)
                return instance(subtype)
            except UnregisteredDependency:
                try:
                    if is_singleton(component):
                        return singleton(component)
                    if (component, caller) in current_env.__instances:
                        return current_env.__instances[(component, caller)]
                    instance = component()
                    current_env.__instances[(component, caller)] = instance
                    return instance
                except TypeError:
                    raise UnregisteredDependency(
                        'No concrete implementation of {} found'.format(
                            str(component)
                        )
                    )
        except RecursionError:
            raise CircularDependency(
                'Circular dependency encountered while injecting {} in {}'.format(
                    str(component),
                    str(caller)
                )
            )

    @staticmethod
    def _find_subtype(component: Type[C]) -> Union[Type[C], Type[S]]:
        def mro_distance(subtype: Type[C]) -> int:
            mro = inspect.getmro(subtype)
            return mro.index(component)

        subtypes = [c for c in Environment._current_env()
                    if issubclass(c, component)]
        distances = [mro_distance(subtype) for subtype in subtypes]
        counter = Counter(distances)
        if any(count > 1 for count in counter.values()):
            ambiguous = [str(subtype) for subtype in subtypes
                         if counter[mro_distance(subtype)] > 1]
            message = ('Attempt to inject type {} with '
                       'equally specific provided subtypes: {}')
            message = message.format(
                str(component),
                ', '.join(ambiguous)
            )
            raise AmbiguousDependencies(message)
        if not subtypes:
            raise UnregisteredDependency(
                'Unregistered dependency: {}'.format(str(component))
            )
        return max(subtypes, key=mro_distance)


__all__ = ['Environment']
