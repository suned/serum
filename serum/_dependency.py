from typing import TypeVar


T2 = TypeVar('T2')


def dependency(cls: T2) -> T2:
    """
    Decorator for types that should be instantiated by serum

    @dependency
    class MyDependency:
        pass

    @inject
    class Dependent:
        dependency: MyDependency

    assert isinstance(Dependent().dependency, MyDependency)
    """
    cls.__dependency__ = True  # type: ignore
    return cls


def singleton(cls: T2) -> T2:
    """
    Decorator for types that should be instantiated by serum and treated as a
    singleton
    """
    cls = dependency(cls)
    cls.__singleton__ = True  # type: ignore
    return cls


__all__ = ['dependency', 'singleton']
