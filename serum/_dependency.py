import inspect

from typing import GenericMeta

from serum._key import Key
from .exceptions import InvalidDependency


def _check_init(dct):
    if '__init__' not in dct:
        return
    init = dct['__init__']
    signature = inspect.signature(init)
    if len(signature.parameters) == 1:
        return
    if not hasattr(init, '__is_inject__'):
        raise InvalidDependency(
            '__init__ method of Dependency subclasses that takes parameters'
            ' must be decorated with inject'
        )
    not_all_parameters_are_annotated_error = InvalidDependency(
            '__init__ method of Dependency subclasses that takes parameters'
            ' must have all parameters except "self" annotated with Dependency'
            ' types or Key'
        )
    if not hasattr(init, '__annotations__'):
        raise not_all_parameters_are_annotated_error
    dependency_annotations = [a for a in init.__annotations__.values()
                              if isinstance(a, Key) or issubclass(a, Dependency)]
    # -1 because of self
    if len(signature.parameters) - 1 != len(dependency_annotations):
        raise not_all_parameters_are_annotated_error


class _DependencyMeta(GenericMeta):
    def __new__(mcs, name, bases, dct):
        _check_init(dct)
        return GenericMeta.__new__(mcs, name, bases, dct)


class Dependency(metaclass=_DependencyMeta):
    """
    Base class for all injectable types.
    Prevents __init__ method with more than one parameter:

    class MyComponent(Component):  # raises: InvalidComponent
        def __init__(self, a):
            pass

    In addition, Components can be abstract, meaning they
    work with the built abc module:

    class MyAbstractComponent(Component):
        @abstractmethod
        def method(self):
            pass

    MyAbstractComponent()  # raises: TypeError
    """


class Singleton(Dependency):
    """
    Base class for singleton types. References to singletons always refer to
    the same instance:

    class ExpensiveObject(Singleton):
        pass

    class Dependent:
        expensive_instance = inject(ExpensiveObject)

    with Environment():
        instance1 = Dependent()
        instance2 = Dependent()
        assert instance1.expensive_instance == instance2.expensive_instance
    """
    pass


__all__ = ['Dependency', 'Singleton']
