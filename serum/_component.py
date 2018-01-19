from abc import ABCMeta
from ._exceptions import InvalidComponent


class _ComponentMeta(ABCMeta):
    def __new__(mcs, name, bases, dct):
        if "__init__" in dct:
            raise InvalidComponent("Components should not have an __init__ method")
        return ABCMeta.__new__(mcs, name, bases, dct)


class Component(metaclass=_ComponentMeta):
    pass


__all__ = ['Component']
