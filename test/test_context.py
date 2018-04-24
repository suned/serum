from serum import Context, dependency, singleton, inject
from serum._dependency_configuration import DependencyConfiguration
from serum.exceptions import (
    AmbiguousDependencies,
    CircularDependency,
    NoNamedDependency)
import threading
import pytest


@dependency
class SomeComponent:
    pass


@dependency
class SomeOtherComponent:
    pass


@dependency
class BaseDependency:
    pass


class ConcreteComponent(BaseDependency):
    def m(self):
        pass


class AlternativeComponent(BaseDependency):
    def m(self):
        pass


@singleton
class SomeSingleton:
    pass


class Key:
    pass


@inject
class Dependent:
    some_singleton: SomeSingleton
    some_component: SomeComponent


def configuration(d):
    return DependencyConfiguration(
        name='test_name',
        dependency=d,
        owner=object()
    )


def test_can_register_dependency():
    e = Context(SomeComponent)
    assert SomeComponent in e


def test_provides_concrete_dependency():
    with Context():
        c = Context.provide(configuration(SomeComponent))
        assert isinstance(c, SomeComponent)


def test_provides_concrete_subclass():
    with Context(ConcreteComponent):
        c = Context.provide(configuration(BaseDependency))
        assert isinstance(c, BaseDependency)
        assert isinstance(c, ConcreteComponent)


def test_provides_correct_implementation():
    with Context(ConcreteComponent):
        c = Context.provide(configuration(BaseDependency))
        assert isinstance(c, BaseDependency)
        assert isinstance(c, ConcreteComponent)
    with Context(AlternativeComponent):
        c = Context.provide(configuration(BaseDependency))
        assert isinstance(c, BaseDependency)
        assert isinstance(c, AlternativeComponent)


def test_intersection():
    e1 = Context(SomeComponent)
    e2 = Context(ConcreteComponent)
    e3 = e1 | e2
    assert SomeComponent in e3
    assert ConcreteComponent in e3


def test_decorater():
    test_environment = Context(SomeComponent)

    @test_environment
    def test():
        component = Context.provide(configuration(SomeComponent))
        assert isinstance(component, SomeComponent)

        test()


def test_new_environment_in_thread():
    def test():
        with Context(AlternativeComponent):
            c1 = Context.provide(configuration(BaseDependency))
            assert isinstance(c1, AlternativeComponent)

    with Context(ConcreteComponent):
        threading.Thread(target=test).start()
        c2 = Context.provide(configuration(BaseDependency))
        assert isinstance(c2, ConcreteComponent)


def test_same_context_in_thread():
    e = Context(ConcreteComponent)

    def test():
        assert e is not Context.current_context()

    with e:
        threading.Thread(target=test).start()


def test_context_manager():
    e = Context()
    with e:
        assert Context.current_context() is e
    assert Context.current_context() is not e


def test_missing_named_dependency():
    c = Context()
    pytest.raises(NoNamedDependency, lambda: c['key'])


def test_getitem():
    e = Context(key='value')
    assert e['key'] == 'value'


def test_gets_most_specific():
    class ConcreteComponentSub(ConcreteComponent):
        pass

    with Context(ConcreteComponent, ConcreteComponentSub):
        c = Context.provide(configuration(BaseDependency))
        assert isinstance(c, ConcreteComponentSub)


def test_fails_with_ambiguous_dependencies():
    with Context(ConcreteComponent, AlternativeComponent):
        with pytest.raises(AmbiguousDependencies):
            Context.provide(configuration(BaseDependency))


def test_singleton_is_always_same_instance():
    with Context():
        s1 = Context.provide(configuration(SomeSingleton))
        s2 = Context.provide(configuration(SomeSingleton))
        assert s1 is s2


def test_circular_dependency():
    @dependency
    class AbstractA:
        pass

    @dependency
    class AbstractB:
        pass

    @inject
    class A(AbstractA):
        b: AbstractB

        def __init__(self):
            self.b

    @inject
    class B(AbstractB):
        a: AbstractA

        def __init__(self):
            self.a

    @inject
    class Dependent:
        a: AbstractA

    with Context(A, B):
        pytest.raises(CircularDependency, lambda: Dependent().a)


def test_subtype_is_singleton():
    @singleton
    class SomeComponentSingleton(SomeComponent):
        pass

    with Context(SomeComponentSingleton):
        s1 = Context.provide(configuration(SomeComponent))
        s2 = Context.provide(configuration(SomeComponent))
        assert s1 is s2
        s3 = Context.provide(configuration(SomeComponentSingleton))
        assert s1 is s3
