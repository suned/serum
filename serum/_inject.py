import inspect
from typing import TypeVar

from functools import wraps

from serum._dependency_configuration import DependencyConfiguration
from serum.exceptions import InjectionError
from ._key import Key
from ._context import provide, current_context
from ._injected_dependency import Dependency as InjectedDependency

T = TypeVar('T')


def __format_name(cls, name):
    return f'_{cls.__name__}__{name}'


def __is_dependency_decorated(dependency):
    is_dependency = hasattr(dependency, '__dependency__')
    return is_dependency


def __set_dependency(configuration: DependencyConfiguration, kwargs, name):
    if configuration.name in kwargs:
        setattr(configuration.owner, name, kwargs[configuration.name])
        del kwargs[configuration.name]
    else:
        try:
            instance = provide(configuration)
        except Exception as e:
            instance = e
        try:
            setattr(configuration.owner, name, instance)
        except Exception as e:
            raise InjectionError(
                f'Could not set attribute {configuration.name} on '
                f'{configuration.owner}'
            ) from e


def _set_base_dependencies(bases, kwargs, self):
    for base in bases:
        if hasattr(base, '__dependencies__'):
            for annotated_name, name, dependency in base.__dependencies__:
                if hasattr(self, name):
                    # if 'self' already has 'name', then it was overwritten
                    # and should not be reset with a type from
                    # a base class
                    continue
                configuration = DependencyConfiguration(
                    dependency=dependency,
                    name=annotated_name,
                    owner=self
                )
                __set_dependency(
                    configuration,
                    kwargs,
                    name,
                )
        _set_base_dependencies(base.__bases__, kwargs, self)


def __decorate_init(init):
    @wraps(init)
    def decorator(self, *args, **kwargs):
        for annotated_name, name, dependency in self.__dependencies__:
            configuration = DependencyConfiguration(
                dependency=dependency,
                name=annotated_name,
                owner=self
            )
            __set_dependency(configuration, kwargs, name)
        bases = self.__class__.__bases__
        _set_base_dependencies(bases, kwargs, self)
        return init(self, *args, **kwargs)
    return decorator


def _decorate_class(cls):
    if not hasattr(cls, '__annotations__'):
        return cls
    dependencies = []
    for name, dependency in cls.__annotations__.items():
        if __is_dependency_decorated(dependency):
            formatted_name = __format_name(cls, name)
            dependencies.append((name, formatted_name, dependency))
            setattr(cls, name, InjectedDependency(formatted_name))
        else:
            formatted_name = __format_name(cls, name)
            key = Key(name=name, dependency_type=dependency)
            dependencies.append((name, formatted_name, key))
            setattr(cls, name, InjectedDependency(formatted_name))
    cls.__dependencies__ = dependencies
    cls.__init__ = __decorate_init(cls.__init__)
    return cls


def _decorate_function(f):
    signature = inspect.signature(f)
    names = signature.parameters.keys()

    @wraps(f)
    def decorator(*args, **kwargs):
        positional_names = {name for name, arg in zip(names, args)}
        dependency_args = kwargs
        annotations = f.__annotations__
        annotations.pop('return', None)
        for name, dependency in annotations.items():
            if name in dependency_args or name in positional_names:
                continue
            if __is_dependency_decorated(dependency):
                configuration = DependencyConfiguration(
                    dependency=dependency,
                    name=name,
                    owner=f
                )
                dependency_args[name] = provide(configuration)
            elif name in current_context():
                key = Key(
                    dependency_type=dependency,
                    name=name
                )
                configuration = DependencyConfiguration(
                    dependency=key,
                    name=name,
                    owner=f
                )
                dependency_args[name] = provide(configuration)
        for name in names:
            if (name in current_context()
                    and name not in dependency_args
                    and name not in positional_names):
                key = Key(
                    dependency_type=object,
                    name=name
                )
                configuration = DependencyConfiguration(
                    dependency=key,
                    name=name,
                    owner=f
                )
                dependency_args[name] = provide(configuration)
        return f(*args, **dependency_args)
    decorator.__is_inject__ = True
    return decorator


def inject(value):
    """
    Decorator for a class or function in which you want to inject dependencies

    @inject
    def f(dependency):
        assert dependency == 'dependency'

    with Environment(dependency='dependency'):
        f()
    """
    if inspect.isclass(value):
        return _decorate_class(value)
    if inspect.isfunction(value) or inspect.ismethod(value):
        return _decorate_function(value)
    return value


__all__ = ['inject']
