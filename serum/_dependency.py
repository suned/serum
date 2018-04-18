from typing import Type, TypeVar


T2 = TypeVar('T2')


def dependency(cls: T2) -> T2:
    cls.__dependency__ = True  # type: ignore
    return cls


def singleton(cls: T2) -> T2:
    cls = dependency(cls)
    cls.__singleton__ = True  # type: ignore
    return cls


__all__ = ['dependency', 'singleton']
