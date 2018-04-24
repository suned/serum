import unittest

from serum import Context, dependency, singleton, inject
from serum._dependency_configuration import DependencyConfiguration
from serum.exceptions import (
    AmbiguousDependencies,
    CircularDependency,
    NoNamedDependency)
import threading


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


class ContextTests(unittest.TestCase):
    def test_can_register_dependency(self):
        e = Context(SomeComponent)
        self.assertTrue(SomeComponent in e)

    def test_provides_concrete_dependency(self):
        with Context():
            c = Context.provide(configuration(SomeComponent))
            self.assertIsInstance(c, SomeComponent)

    def test_provides_concrete_subclass(self):
        with Context(ConcreteComponent):
            c = Context.provide(configuration(BaseDependency))
            self.assertIsInstance(c, BaseDependency)
            self.assertIsInstance(c, ConcreteComponent)

    def test_provides_correct_implementation(self):
        with Context(ConcreteComponent):
            c = Context.provide(configuration(BaseDependency))
            self.assertIsInstance(c, BaseDependency)
            self.assertIsInstance(c, ConcreteComponent)
        with Context(AlternativeComponent):
            c = Context.provide(configuration(BaseDependency))
            self.assertIsInstance(c, BaseDependency)
            self.assertIsInstance(c, AlternativeComponent)

    def test_intersection(self):
        e1 = Context(SomeComponent)
        e2 = Context(ConcreteComponent)
        e3 = e1 | e2
        self.assertIn(SomeComponent, e3)
        self.assertIn(ConcreteComponent, e3)

    def test_decorater(self):
        test_environment = Context(SomeComponent)

        @test_environment
        def test():
            component = Context.provide(configuration(SomeComponent))
            self.assertIsInstance(component, SomeComponent)

        test()

    def test_new_environment_in_thread(self):
        def test():
            with Context(AlternativeComponent):
                c1 = Context.provide(configuration(BaseDependency))
                self.assertIsInstance(c1, AlternativeComponent)

        with Context(ConcreteComponent):
            threading.Thread(target=test).start()
            c2 = Context.provide(configuration(BaseDependency))
            self.assertIsInstance(c2, ConcreteComponent)

    def test_same_context_in_thread(self):
        e = Context(ConcreteComponent)

        def test():
            self.assertIsNot(e, Context.current_context())

        with e:
            threading.Thread(target=test).start()

    def test_context_manager(self):
        e = Context()
        with e:
            self.assertIs(Context.current_context(), e)
        self.assertIsNot(Context.current_context(), e)

    def test_missing_named_dependency(self):
        c = Context()
        self.assertRaises(NoNamedDependency, lambda: c['key'])

    def test_getitem(self):
        e = Context(key='value')
        self.assertEqual(e['key'], 'value')

    def test_gets_most_specific(self):
        class ConcreteComponentSub(ConcreteComponent):
            pass

        with Context(ConcreteComponent, ConcreteComponentSub):
            c = Context.provide(configuration(BaseDependency))
            self.assertIsInstance(c, ConcreteComponentSub)

    def test_fails_with_ambiguous_dependencies(self):
        with Context(ConcreteComponent, AlternativeComponent):
            with self.assertRaises(AmbiguousDependencies):
                Context.provide(configuration(BaseDependency))

    def test_singleton_is_always_same_instance(self):
        with Context():
            s1 = Context.provide(configuration(SomeSingleton))
            s2 = Context.provide(configuration(SomeSingleton))
            self.assertIs(s1, s2)

    def test_circular_dependency(self):
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
            self.assertRaises(CircularDependency, lambda: Dependent().a)

    def test_subtype_is_singleton(self):
        @singleton
        class SomeComponentSingleton(SomeComponent):
            pass
        with Context(SomeComponentSingleton):
            s1 = Context.provide(configuration(SomeComponent))
            s2 = Context.provide(configuration(SomeComponent))
            self.assertIs(s1, s2)
            s3 = Context.provide(configuration(SomeComponentSingleton))
            self.assertIs(s1, s3)
