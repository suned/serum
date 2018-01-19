from abc import ABCMeta
from ._exceptions import InvalidComponent


class _ComponentMeta(ABCMeta):
    def __new__(mcs, name, bases, dct):
        if "__init__" in dct:
            raise InvalidComponent("Components should not have an __init__ method")
        return ABCMeta.__new__(mcs, name, bases, dct)


class Component(metaclass=_ComponentMeta):
    """
    Base class for all injectable types.
    Prevents __init__ method:

    class MyComponent(Component):  # raises: InvalidComponent
        def __init__(self):
            pass

    In addition, Components can be abstract, meaning they
    work with the built abc module:

    class MyAbstractComponent(Component):
        @abstractmethod
        def method(self):
            pass

    MyAbstractComponent()  # raises: TypeError
    """
    pass


__all__ = ['Component']
