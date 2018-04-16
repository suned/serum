from typing import Type


def dependency(cls: Type[object]):
    cls.__is_dependency__ = True
    return cls


def singleton(cls: Type[object]):
    cls = dependency(cls)
    cls.__is_singleton__ = True
    return cls


__all__ = ['dependency', 'singleton']
