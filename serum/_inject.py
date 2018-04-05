import inspect
from typing import Type, TypeVar, cast

from functools import wraps

from ._key import Key
from ._environment import provide
from ._dependency import Dependency
from ._injected_dependency import Dependency as InjectedDependency

T = TypeVar('T')


def __format_name(cls, name):
    return f'_{cls.__name__}__{name}'


def __decorate_init(init):
    @wraps(init)
    def decorator(self, *args, **kwargs):
        for name, dependency in self.__dependencies__:
            setattr(self, name, provide(dependency))
        for base in self.__class__.__bases__:
            if hasattr(base, '__dependencies__'):
                for name, dependency in base.__dependencies__:
                    if hasattr(self, name):
                        # if self already has name, then it was overwritten
                        continue
                    setattr(self, name, provide(dependency))
        return init(self, *args, **kwargs)
    return decorator


def _decorate_class(cls):
    if not hasattr(cls, '__annotations__'):
        return cls
    dependencies = []
    for name, dependency in cls.__annotations__.items():
        if isinstance(dependency, Key):
            formatted_name = __format_name(cls, name)
            key = Key(name=name, dependency_type=dependency.dependency_type)
            dependencies.append((formatted_name, key))
            setattr(cls, name, InjectedDependency(formatted_name))
        elif issubclass(dependency, Dependency):
            formatted_name = __format_name(cls, name)
            dependencies.append((formatted_name, dependency))
            setattr(cls, name, InjectedDependency(formatted_name))
    if dependencies:
        cls.__dependencies__ = dependencies
        cls.__init__ = __decorate_init(cls.__init__)
    return cls


def _decorate_function(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        dependency_args = {}
        for name, dependency in f.__annotations__.items():
            if isinstance(dependency, Key):
                key = Key(
                    name=name,
                    dependency_type=dependency.dependency_type
                )
                dependency_args[name] = provide(key)
            elif issubclass(dependency, Dependency):
                dependency_args[name] = provide(dependency)
        dependency_args.update(kwargs)
        return f(*args, **dependency_args)
    decorator.__is_inject__ = True
    return decorator


class Inject:
    def __call__(self, value):
        if inspect.isclass(value):
            return _decorate_class(value)
        if inspect.isfunction(value) or inspect.ismethod(value):
            return _decorate_function(value)
        return value

    # noinspection PyMethodMayBeStatic
    def name(self, of_type: Type[T] = object) -> Type[T]:
        key = Key(dependency_type=of_type)
        return cast(Type[T], key)


inject = Inject()


__all__ = ['inject']
