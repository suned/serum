from copy import copy, deepcopy
from unittest.mock import create_autospec, MagicMock
from functools import wraps
from typing import Type, Set, Union, Dict, TypeVar

from ._dependency_configuration import DependencyConfiguration
from ._key import Key
from .exceptions import NoNamedDependency, InjectionError
from .exceptions import (
    AmbiguousDependencies,
    CircularDependency)
import threading
import inspect
from collections import Counter


T = TypeVar('T')


class _LocalStorage(threading.local):
    def __init__(self):
        self.current_env: Environment = None


class _EnvironmentState(threading.local):
    def __init__(self):
        self.pending: Set[Type[object]] = set()
        self.old_current: Environment = None
        self.mocks: Dict[Union[str, Type[object]], MagicMock] = dict()
        self.singletons: Dict[Type[T], T] = dict()

    def __deepcopy__(self, memodict):
        new = _EnvironmentState()
        new.pending = copy(self.pending)
        new.old_current = copy(self.old_current)
        new.mocks = copy(self.mocks)
        new.singletons = copy(self.mocks)
        return new


class Environment:
    """
    Context manager/decorator for providing dependencies:

    with Environment(MyDependency):
        NeedsDependency()
    or

    @Environment(MyDependency):
    def fun():
        NeedsDependency()
    """
    __local_storage = _LocalStorage()

    @staticmethod
    def current_env() -> 'Environment':
        env = Environment.__local_storage.current_env
        if env is None:
            return Environment()
        return env

    @staticmethod
    def mock(dependency: Union[str, Type[object]]):
        current_env = Environment.current_env()
        if isinstance(dependency, str):
            value = current_env[dependency]
            mock = create_autospec(value)
        else:
            mock = create_autospec(dependency, instance=True)
        current_env.__state.mocks[dependency] = mock
        return mock

    @staticmethod
    def _set_current_env(env: 'Environment'):
        Environment.__local_storage.current_env = env

    def __init__(self, *args: Type[object], **kwargs: object) -> None:
        """
        Construct a new environment
        :param args: Dependency decorated types to provide in this environment
        :param kwargs: Named dependencies to provide in this environment
        """
        self.__registry: Set[Type[object]] = set()
        self.__state: _EnvironmentState = _EnvironmentState()
        self.__named_dependencies = kwargs
        self.__old_current = None
        for c in args:
            self.__use(c)

    def __getitem__(self, item: str):
        """
        Get named dependency in this environment
        :param item: Name of dependency
        :return: dependency
        """
        if self.is_mocked(item):
            return self.__state.mocks[item]
        try:
            return self.__named_dependencies[item]
        except KeyError:
            raise NoNamedDependency(
                f'Named dependency "{item}" not found in: {repr(self)}'
            )

    @property
    def pending(self) -> Set[Type[object]]:
        return self.__state.pending

    def get_mock(self, component: Type[object]) -> MagicMock:
        return self.__state.mocks[component]

    def is_mocked(self, component: Union[str, Type[object]]) -> bool:
        return component in self.__state.mocks

    def __use(self, component: Type[object]) -> 'Environment':
        self.__registry.add(component)
        return self

    def __contains__(self, component: Type[object]) -> bool:
        """
        Test if a Dependency is registered in this environment
        :param component: Dependency to test
        :return: True if component is registered in this environment else False
        """
        if isinstance(component, str):
            return component in self.__named_dependencies
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
        Iterate over the dependencies registered in this environment
        :return: Iterator of components
        """
        return iter(self.__registry)

    def __or__(self, other: 'Environment') -> 'Environment':
        """
        Combine this environment with another, such that the new environment
        can provide all dependencies in both environments
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
        self.__old_current = Environment.current_env()
        old_state = self.__old_current.__copy_state()
        self.__set_state(old_state)
        Environment._set_current_env(self)
        return self

    def __set_state(self, state):
        self.__state = state

    def __copy_state(self):
        return deepcopy(self.__state)

    def has_singleton_instance(self, singleton_type):
        return singleton_type in self.__state.singletons

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        De-register this environment as the current environment in this thread
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self.__state.__init__()
        Environment._set_current_env(self.__old_current)
        self.__old_current = None

    @staticmethod
    def provide(configuration: DependencyConfiguration) -> Union[T, MagicMock]:
        """
        Provide a dependency in this environment
        :param configuration: The type to provide
        :return: Instance of the most specific subtype of component
                 in this environment
        """
        environment = Environment.current_env()

        def singleton(singleton_type: Type[T]) -> T:
            if environment.has_singleton_instance(singleton_type):
                return environment.get_singleton(singleton_type)
            else:
                singleton_instance = singleton_type()
                environment.add_singleton(
                    singleton_type,
                    singleton_instance
                )
                return singleton_instance

        def instance(component_type: Type[T]) -> T:
            component_instance = component_type()
            return component_instance

        def is_singleton(st):
            return hasattr(st, '__singleton__')

        def instantiate(dependency_type: Type[T]) -> T:
            if dependency_type in environment.pending:
                raise CircularDependency(
                    f'Circular dependency encountered while injecting '
                    f'{dependency_type} as "{configuration.name}" in '
                    f'{configuration.owner}'
                    )
            environment.pending.add(dependency_type)
            try:
                if is_singleton(dependency_type):
                    component_instance = singleton(dependency_type)
                else:
                    component_instance = instance(dependency_type)
                return component_instance
            except CircularDependency:
                raise
            except Exception as e:
                raise InjectionError(
                    f'Could not instantiate {dependency_type} when injecting '
                    f'"{configuration.name}" in {configuration.owner}.'
                ) from e
            finally:
                environment.pending.remove(dependency_type)
        dependency: Type[T] = configuration.dependency
        if environment.is_mocked(dependency):
            return environment.get_mock(dependency)
        subtype = Environment.find_subtype(dependency)
        if subtype is None:
            return instantiate(dependency)
        return instantiate(subtype)

    @staticmethod
    def find_subtype(component: Type[T]) -> Union[Type[T], None]:
        def mro_distance(subtype: Type[T]) -> int:
            mro = inspect.getmro(subtype)
            return mro.index(component)

        subtypes = [c for c in Environment.current_env()
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
            return None
        return max(subtypes, key=mro_distance)

    def get_singleton(self, singleton_type):
        return self.__state.singletons[singleton_type]

    def add_singleton(self, singleton_type, instance):
        self.__state.singletons[singleton_type] = instance

    def __repr__(self):
        dependencies = [repr(dependency) for dependency in self.__registry]
        named_dependencies = [f'{key}={repr(value)}' for key, value
                              in self.__named_dependencies.items()]
        args = ', '.join(dependencies + named_dependencies)
        return f'Environment({args})'


__all__ = ['Environment']


def provide(configuration: DependencyConfiguration):
    if isinstance(configuration.dependency, Key):
        return Environment.current_env()[configuration.name]
    return Environment.provide(configuration)


def current_env():
    return Environment.current_env()
