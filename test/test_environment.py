import unittest

from serum import Environment, dependency, singleton, inject
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


class EnvironmentTests(unittest.TestCase):
    def test_can_register_dependency(self):
        e = Environment(SomeComponent)
        self.assertTrue(SomeComponent in e)

    def test_environment_provides_concrete_dependency(self):
        with Environment():
            c = Environment.provide(configuration(SomeComponent))
            self.assertIsInstance(c, SomeComponent)

    def test_environment_provides_concrete_subclass(self):
        with Environment(ConcreteComponent):
            c = Environment.provide(configuration(BaseDependency))
            self.assertIsInstance(c, BaseDependency)
            self.assertIsInstance(c, ConcreteComponent)

    def test_environment_provides_correct_implementation(self):
        with Environment(ConcreteComponent):
            c = Environment.provide(configuration(BaseDependency))
            self.assertIsInstance(c, BaseDependency)
            self.assertIsInstance(c, ConcreteComponent)
        with Environment(AlternativeComponent):
            c = Environment.provide(configuration(BaseDependency))
            self.assertIsInstance(c, BaseDependency)
            self.assertIsInstance(c, AlternativeComponent)

    def test_intersection(self):
        e1 = Environment(SomeComponent)
        e2 = Environment(ConcreteComponent)
        e3 = e1 | e2
        self.assertIn(SomeComponent, e3)
        self.assertIn(ConcreteComponent, e3)

    def test_decorater(self):
        test_environment = Environment(SomeComponent)

        @test_environment
        def test():
            component = Environment.provide(configuration(SomeComponent))
            self.assertIsInstance(component, SomeComponent)

        test()

    def test_new_environment_in_thread(self):
        def test():
            with Environment(AlternativeComponent):
                c1 = Environment.provide(configuration(BaseDependency))
                self.assertIsInstance(c1, AlternativeComponent)

        with Environment(ConcreteComponent):
            threading.Thread(target=test).start()
            c2 = Environment.provide(configuration(BaseDependency))
            self.assertIsInstance(c2, ConcreteComponent)

    def test_same_environment_in_thread(self):
        e = Environment(ConcreteComponent)

        def test():
            self.assertIsNot(e, Environment.current_env())

        with e:
            threading.Thread(target=test).start()

    def test_context_manager(self):
        e = Environment()
        with e:
            self.assertIs(Environment.current_env(), e)
        self.assertIsNot(Environment.current_env(), e)

    def test_missing_named_dependency(self):
        e = Environment()
        with self.assertRaises(NoNamedDependency):
            _ = e['key']

    def test_getitem(self):
        e = Environment(key='value')
        self.assertEqual(e['key'], 'value')

    def test_environment_gets_most_specific(self):
        class ConcreteComponentSub(ConcreteComponent):
            pass

        with Environment(ConcreteComponent, ConcreteComponentSub):
            c = Environment.provide(configuration(BaseDependency))
            self.assertIsInstance(c, ConcreteComponentSub)

    def test_fails_with_ambiguous_dependencies(self):
        with Environment(ConcreteComponent, AlternativeComponent):
            with self.assertRaises(AmbiguousDependencies):
                Environment.provide(configuration(BaseDependency))

    def test_singleton_is_always_same_instance(self):
        with Environment():
            s1 = Environment.provide(configuration(SomeSingleton))
            s2 = Environment.provide(configuration(SomeSingleton))
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

        with Environment(A, B):
            with self.assertRaises(CircularDependency):
                _ = Dependent().a

    def test_subtype_is_singleton(self):
        @singleton
        class SomeComponentSingleton(SomeComponent):
            pass
        with Environment(SomeComponentSingleton):
            s1 = Environment.provide(configuration(SomeComponent))
            s2 = Environment.provide(configuration(SomeComponent))
            self.assertIs(s1, s2)
            s3 = Environment.provide(configuration(SomeComponentSingleton))
            self.assertIs(s1, s3)
