from copy import copy, deepcopy
from unittest.mock import create_autospec, MagicMock
from functools import wraps
from typing import Type, Set, Union, Dict, TypeVar  # noqa

from ._dependency_configuration import DependencyConfiguration
from ._key import Key
from .exceptions import NoNamedDependency, InjectionError
from .exceptions import (
    AmbiguousDependencies,
    CircularDependency)
import threading
import inspect
from collections import Counter


__all__ = ['Context']


T = TypeVar('T')


class _LocalStorage(threading.local):
    def __init__(self):
        self.current_env = None  # type: Context


class _ContextState(threading.local):
    def __init__(self):
        self.pending = set()  # type: Set[object]
        self.old_current = None  # type: Context
        self.mocks = dict()  # type: Dict[Union[str, object], MagicMock]
        self.singletons = dict()  # type: Dict[T, T]

    def __deepcopy__(self, memodict):
        new = _ContextState()
        new.pending = copy(self.pending)
        new.old_current = copy(self.old_current)
        new.mocks = copy(self.mocks)
        new.singletons = copy(self.mocks)
        return new


class Context:
    """
    Context manager/decorator for providing dependencies:

    with Context(MyDependency):
        NeedsDependency()
    or

    @Context(MyDependency):
    def fun():
        NeedsDependency()
    """
    __local_storage = _LocalStorage()

    @staticmethod
    def current_context() -> 'Context':
        env = Context.__local_storage.current_env
        if env is None:
            return Context()
        return env

    @staticmethod
    def mock(dependency: Union[str, object]):
        current_env = Context.current_context()
        if isinstance(dependency, str):
            value = current_env[dependency]
            mock = create_autospec(value)
        else:
            mock = create_autospec(dependency, instance=True)
        current_env.__state.mocks[dependency] = mock
        return mock

    @staticmethod
    def _set_current_env(env: 'Context'):
        Context.__local_storage.current_env = env

    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Construct a new context
        :param args: Dependency decorated types to provide in this context
        :param kwargs: Named dependencies to provide in this context
        """
        self.__registry = set()  # type: Set[object]
        self.__state = _ContextState()  # type: _ContextState
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
                'Named dependency "{item}" not found!}'.format(item=item)
            )

    @property
    def pending(self) -> Set[object]:
        return self.__state.pending

    def get_mock(self, component: object) -> MagicMock:
        return self.__state.mocks[component]

    def is_mocked(self, component: Union[str, object]) -> bool:
        return component in self.__state.mocks

    def __use(self, component: object) -> 'Context':
        self.__registry.add(component)
        return self

    def __contains__(self, component: object) -> bool:
        """
        Test if a Dependency is registered in this context
        :param component: Dependency to test
        :return: True if component is registered in this environment else False
        """
        if isinstance(component, str):
            return component in self.__named_dependencies
        return component in self.__registry

    def __call__(self, f):
        """
        Decorate a function to run in this context
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
        Iterate over the dependencies registered in this context
        :return: Iterator of components
        """
        return iter(self.__registry)

    def __or__(self, other: 'Context') -> 'Context':
        """
        Combine this environment with another, such that the new context
        can provide all dependencies in both contexts
        :param other: context to combine with this one
        :return: New context with components from this and the other
                 environment
        """
        new_registry = self.__registry | other.__registry
        return Context(*new_registry)

    def __enter__(self):
        """
        Register this context as the current environment in this thread
        :return:
        """
        self.__old_current = Context.current_context()
        old_state = self.__old_current.__copy_state()
        self.__set_state(old_state)
        Context._set_current_env(self)
        return self

    def __set_state(self, state):
        self.__state = state

    def __copy_state(self):
        return deepcopy(self.__state)

    def has_singleton_instance(self, singleton_type):
        return singleton_type in self.__state.singletons

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        De-register this context as the current environment in this thread
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self.__state.__init__()
        Context._set_current_env(self.__old_current)
        self.__old_current = None

    @staticmethod
    def provide(configuration: DependencyConfiguration) -> Union[T, MagicMock]:
        """
        Provide a dependency in this context
        :param configuration: The type to provide
        :return: Instance of the most specific subtype of component
                 in this environment
        """
        context = Context.current_context()

        def singleton(singleton_type: T) -> T:
            if context.has_singleton_instance(singleton_type):
                return context.get_singleton(singleton_type)
            else:
                singleton_instance = singleton_type()
                context.add_singleton(
                    singleton_type,
                    singleton_instance
                )
                return singleton_instance

        def instance(component_type: T) -> T:
            component_instance = component_type()
            return component_instance

        def is_singleton(st):
            return hasattr(st, '__singleton__')

        def instantiate(dependency_type: T) -> T:
            if dependency_type in context.pending:
                raise CircularDependency(
                    'Circular dependency encountered while injecting {type} as "{name}" in {owner}'
                    .format(type=dependency_type, name=configuration.name, owner=configuration.owner)
                )
            context.pending.add(dependency_type)
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
                    'Could not instantiate {type} when injecting "{name}" in {owner}'
                    .format(type=dependency_type, name=configuration.name, owner=configuration.owner)
                ) from e
            finally:
                context.pending.remove(dependency_type)
        dependency = configuration.dependency  # type: T
        if context.is_mocked(dependency):
            return context.get_mock(dependency)
        subtype = Context.find_subtype(dependency)
        if subtype is None:
            return instantiate(dependency)
        return instantiate(subtype)

    @staticmethod
    def find_subtype(component: T) -> Union[T, None]:
        def mro_distance(subtype: T) -> int:
            mro = inspect.getmro(subtype)
            return mro.index(component)

        subtypes = [c for c in Context.current_context()
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
        named_dependencies = ['{key}={value}'.format(key=key, value=repr(value)) for key, value
                              in self.__named_dependencies.items()]
        args = ', '.join(dependencies + named_dependencies)
        return 'Context({args})'.format(args=args)


def provide(configuration: DependencyConfiguration):
    if isinstance(configuration.dependency, Key):
        return Context.current_context()[configuration.name]
    return Context.provide(configuration)


def current_context():
    return Context.current_context()
