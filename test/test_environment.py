import unittest

import warnings

from serum import Environment, Dependency, abstractmethod, Singleton, inject
from serum.exceptions import (
    UnregisteredDependency,
    AmbiguousDependencies,
    CircularDependency,
    NoNamedDependency
)
import threading


class SomeComponent(Dependency):
    pass


class SomeOtherComponent(Dependency):
    pass


class AbstractComponent(Dependency):
    @abstractmethod
    def m(self):
        pass


class ConcreteComponent(AbstractComponent):
    def m(self):
        pass


class AlternativeComponent(AbstractComponent):
    def m(self):
        pass


class SomeSingleton(Singleton):
    pass


class Key:
    pass


@inject
class Dependent:
    some_singleton: SomeSingleton
    some_component: SomeComponent


class EnvironmentTests(unittest.TestCase):
    def test_can_register_dependency(self):
        e = Environment(SomeComponent)
        self.assertTrue(SomeComponent in e)

    def test_environment_provides_concrete_dependency(self):
        with Environment():
            c = Environment.provide(SomeComponent)
            self.assertIsInstance(c, SomeComponent)

    def test_environment_cant_provide_abstract_dependency(self):
        with Environment():
            with self.assertRaises(UnregisteredDependency):
                Environment.provide(AbstractComponent)

    def test_environment_provides_concrete_subclass(self):
        with Environment(ConcreteComponent):
            c = Environment.provide(AbstractComponent)
            self.assertIsInstance(c, AbstractComponent)
            self.assertIsInstance(c, ConcreteComponent)

    def test_environment_provides_correct_implementation(self):
        with Environment(ConcreteComponent):
            c = Environment.provide(AbstractComponent)
            self.assertIsInstance(c, AbstractComponent)
            self.assertIsInstance(c, ConcreteComponent)
        with Environment(AlternativeComponent):
            c = Environment.provide(AbstractComponent)
            self.assertIsInstance(c, AbstractComponent)
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
            component = Environment.provide(SomeComponent)
            self.assertIsInstance(component, SomeComponent)

        test()

    def test_new_environment_in_thread(self):
        def test():
            with Environment(AlternativeComponent):
                c1 = Environment.provide(AbstractComponent)
                self.assertIsInstance(c1, AlternativeComponent)

        with Environment(ConcreteComponent):
            threading.Thread(target=test).start()
            c2 = Environment.provide(AbstractComponent)
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
            c = Environment.provide(AbstractComponent)
            self.assertIsInstance(c, ConcreteComponentSub)

    def test_fails_with_ambiguous_dependencies(self):
        with Environment(ConcreteComponent, AlternativeComponent):
            with self.assertRaises(AmbiguousDependencies):
                Environment.provide(AbstractComponent)

    def test_singleton_is_always_same_instance(self):
        with Environment():
            s1 = Environment.provide(SomeSingleton)
            s2 = Environment.provide(SomeSingleton)
            self.assertIs(s1, s2)

    def test_circular_dependency(self):
        class AbstractA(Dependency):
            pass

        class AbstractB(Dependency):
            pass

        @inject
        class A(AbstractA):
            b: AbstractB

        @inject
        class B(AbstractB):
            a: AbstractA

        @inject
        class Dependent:
            a: AbstractA

        with Environment(A, B):
            with self.assertRaises(CircularDependency):
                Dependent()

    def test_subtype_is_singleton(self):
        class SomeComponentSingleton(SomeComponent, Singleton):
            pass
        with Environment(SomeComponentSingleton):
            s1 = Environment.provide(SomeComponent)
            s2 = Environment.provide(SomeComponent)
            self.assertIs(s1, s2)
            s3 = Environment.provide(SomeComponentSingleton)
            self.assertIs(s1, s3)

    @Environment(key='value')
    def test_warning_issued_when_injecting_named_dependency_with_wrong_type(self):
        @inject
        def f(key: inject.name(of_type=int)):
            pass

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            f()
            self.assertEqual(len(w), 1)
            self.assertIs(w[-1].category, RuntimeWarning)

