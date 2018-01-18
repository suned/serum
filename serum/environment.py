from typing import Type, TypeVar, Set
from .exceptions import InvalidDependency, NoEnvironment, UnregisteredDependency
from .component import Component

C = TypeVar('C', bound=Component)


class Environment:
    __current_env: 'Environment' = None

    def __init__(self, *args: Type[C]) -> None:
        self.__registry: Set = set()
        for c in args:
            self.use(c)

    def use(self, component: Type[C]):
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

    def __enter__(self):
        self.__old_current = Environment.__current_env
        Environment.__current_env = self

    def __exit__(self, exc_type, exc_val, exc_tb):
        Environment.__current_env = self.__old_current
        self.__old_current = None

    @staticmethod
    def get(component: Type[C]) -> C:
        if Environment.__current_env is None:
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
        try:
            return next(c for c in Environment.__current_env.__registry
                        if issubclass(c, component))
        except StopIteration:
            raise UnregisteredDependency(
                'Unregistered dependency: {}'.format(str(component))
            )


__all__ = ['Environment']
