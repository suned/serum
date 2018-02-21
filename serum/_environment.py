from copy import copy, deepcopy
from unittest.mock import create_autospec, MagicMock
from functools import wraps
from typing import Type, TypeVar, Set, Union, Dict
from weakref import WeakKeyDictionary

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


class _LocalStorage(threading.local):
    def __init__(self):
        self.current_env: Environment = None


class _EnvironmentState(threading.local):
    def __init__(self):
        self.pending: Set[Type[C]] = set()
        self.old_current: Environment = None
        self.mocks: Dict[Type[C], MagicMock] = dict()
        self.singletons: Dict[Type[C], C] = dict()
        self.instances: Dict[object, Dict[Type[C], C]] = WeakKeyDictionary()

    def __deepcopy__(self, memodict):
        new = _EnvironmentState()
        new.pending = copy(self.pending)
        new.old_current = copy(self.old_current)
        new.mocks = copy(self.mocks)
        new.singletons = copy(self.mocks)
        new.instances = copy(self.instances)
        return new


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
    def mock(component: Type[C]):
        current_env = Environment._current_env()
        if current_env is None:
            raise NoEnvironment(
                'Can\t register mock outside environment'
            )
        mock = create_autospec(component, instance=True)
        current_env.__state.mocks[component] = mock
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
        self.__state: _EnvironmentState = _EnvironmentState()
        for c in args:
            self.__use(c)

    @property
    def pending(self) -> Set[Type[C]]:
        return self.__state.pending

    def get_mock(self, component: Type[C]) -> MagicMock:
        return self.__state.mocks[component]

    def is_mocked(self, component: Type[C]) -> bool:
        return component in self.__state.mocks

    def __use(self, component: Type[C]) -> 'Environment':
        if not issubclass(component, Component):
            raise InvalidDependency(
                'Attempt to register type that is not a Component: {}'.format(
                    str(component)
                )
            )
        self.__registry.add(component)
        return self

    def __contains__(self, component: Type[C]) -> bool:
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
        if self.__old_current is not None:
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
    def provide(component: Type[C], caller: object) -> Union[C, MagicMock]:
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

        def singleton(singleton_type: Type[C]) -> C:
            if current_env.has_singleton_instance(singleton_type):
                return current_env.get_singleton(singleton_type)
            else:
                singleton_instance = singleton_type()
                current_env.add_singleton(
                    singleton_type,
                    singleton_instance
                )
                return singleton_instance

        def instance(component_type: Type[C]) -> C:
            component_instance = component_type()
            current_env.set_instance(component, caller, component_instance)
            return component_instance

        def is_singleton(st):
            return issubclass(st, Singleton)

        def instantiate(component_type: Type[C]) -> C:
            if is_singleton(component_type):
                return singleton(component_type)
            return instance(component_type)

        if current_env.is_mocked(component):
            return current_env.get_mock(component)
        if current_env.has_instance(component, caller):
            return current_env.get_instance(component, caller)
        try:
            subtype = Environment._find_subtype(component)
            if subtype in current_env.pending:
                raise CircularDependency(
                    'Circular dependency encountered while injecting {} in {}'.format(
                        str(component),
                        str(caller)
                    )
                )
            current_env.pending.add(subtype)
            subtype_instance = instantiate(subtype)
            current_env.pending.remove(subtype)
            return subtype_instance
        except UnregisteredDependency:
            try:
                return instantiate(component)
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

    def get_singleton(self, singleton_type):
        return self.__state.singletons[singleton_type]

    def add_singleton(self, singleton_type, instance):
        self.__state.singletons[singleton_type] = instance

    def has_instance(self, component, caller):
        return caller in self.__state.instances and component in self.__state.instances[caller]

    @property
    def instances(self):
        return self.__state.instances

    def get_instance(self, component, caller):
        return self.__state.instances[caller][component]

    def set_instance(self, component, caller, component_instance):
        if caller not in self.__state.instances:
            self.__state.instances[caller] = {}
        self.__state.instances[caller][component] = component_instance


__all__ = ['Environment']
