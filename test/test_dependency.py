from serum import dependency, singleton


def test_dependency_decorator_adds_flag():
    @dependency
    class Dependency:
        pass
    assert Dependency.__dependency__


def test_singleton():
    @singleton
    class Dependency:
        pass
    assert Dependency.__dependency__
    assert Dependency.__singleton__
