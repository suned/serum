import unittest

import gc

from serum import Environment, Component, abstractmethod, Singleton, inject
from serum.exceptions import InvalidDependency, UnregisteredDependency, \
    NoEnvironment, AmbiguousDependencies, CircularDependency
import threading


class SomeComponent(Component):
    pass


class SomeOtherComponent(Component):
    pass


class AbstractComponent(Component):
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


class Dependent:
    some_component = inject(SomeComponent)


def check_garbage(self, e):
    def _(phase, info):
        if phase == 'stop':
            self.assertEqual(e.instances, {})
    gc.callbacks.append(_)
    gc.collect()
    gc.callbacks.remove(_)


class EnvironmentTests(unittest.TestCase):

    def test_cant_register_non_component(self):
        class NotAComponent:
            pass
        with self.assertRaises(InvalidDependency):
            Environment(NotAComponent, self)

    def test_can_register_component(self):
        e = Environment(SomeComponent)
        self.assertTrue(SomeComponent in e)

    def test_environment_provides_concrete_component(self):
        with Environment():
            c = Environment.provide(SomeComponent, self)
            self.assertIsInstance(c, SomeComponent)

    def test_environment_cant_provide_abstract_component(self):
        with Environment():
            with self.assertRaises(UnregisteredDependency):
                Environment.provide(AbstractComponent, self)

    def test_environment_provides_concrete_subclass(self):
        with Environment(ConcreteComponent):
            c = Environment.provide(AbstractComponent, self)
            self.assertIsInstance(c, AbstractComponent)
            self.assertIsInstance(c, ConcreteComponent)

    def test_environment_provides_correct_implementation(self):
        with Environment(ConcreteComponent):
            c = Environment.provide(AbstractComponent, self)
            self.assertIsInstance(c, AbstractComponent)
            self.assertIsInstance(c, ConcreteComponent)
        with Environment(AlternativeComponent):
            c = Environment.provide(AbstractComponent, self)
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
            component = Environment.provide(SomeComponent, self)
            self.assertIsInstance(component, SomeComponent)

        test()

    def test_new_environment_in_thread(self):
        def test():
            with Environment(AlternativeComponent):
                c1 = Environment.provide(AbstractComponent, self)
                self.assertIsInstance(c1, AlternativeComponent)

        with Environment(ConcreteComponent):
            threading.Thread(target=test).start()
            c2 = Environment.provide(AbstractComponent, self)
            self.assertIsInstance(c2, ConcreteComponent)

    def test_same_environment_in_thread(self):
        def test():
            with self.assertRaises(NoEnvironment):
                Environment.provide(AbstractComponent, self)

        with Environment(ConcreteComponent):
            threading.Thread(target=test).start()

    def test_nested_environments(self):
        with Environment(ConcreteComponent):
            c = Environment.provide(AbstractComponent, self)
            self.assertIsInstance(c, ConcreteComponent)
            with Environment(AlternativeComponent):
                c = Environment.provide(AbstractComponent, self)
                self.assertIsInstance(c, AlternativeComponent)

    def test_context_manager(self):
        e = Environment()
        with e:
            self.assertIs(Environment._current_env(), e)
        self.assertIsNone(Environment._current_env())

    def test_environment_gets_most_specific(self):
        class ConcreteComponentSub(ConcreteComponent):
            pass

        with Environment(ConcreteComponent, ConcreteComponentSub):
            c = Environment.provide(AbstractComponent, self)
            self.assertIsInstance(c, ConcreteComponentSub)

    def test_fails_with_ambiguous_dependencies(self):
        with Environment(ConcreteComponent, AlternativeComponent):
            with self.assertRaises(AmbiguousDependencies):
                Environment.provide(AbstractComponent, self)

    def test_singleton_is_always_same_instance(self):
        with Environment():
            s1 = Environment.provide(SomeSingleton, self)
            s2 = Environment.provide(SomeSingleton, object())
            self.assertIs(s1, s2)

    def test_instances_are_cached(self):
        with Environment():
            s1 = Environment.provide(SomeComponent, self)
            s2 = Environment.provide(SomeComponent, self)
            self.assertIs(s1, s2)

    def test_more_than_one_instance_in_cache(self):
        with Environment():
            s1 = Environment.provide(SomeComponent, self)
            s2 = Environment.provide(SomeOtherComponent, self)
            s3 = Environment.provide(SomeComponent, self)
            s4 = Environment.provide(SomeOtherComponent, self)
            self.assertIs(s1, s3)
            self.assertIs(s2, s4)

    def test_circular_dependency(self):
        class AbstractA(Component):
            pass

        class AbstractB(Component):
            pass

        class A(AbstractA):
            b = inject(AbstractB)

            def __init__(self):
                self.b

        class B(AbstractB):
            a = inject(AbstractA)

            def __init__(self):
                self.a

        class Dependent:
            a = inject(AbstractA)

        with Environment(A, B):
            with self.assertRaises(CircularDependency):
                Dependent().a

    def test_subtype_is_singleton(self):
        class SomeComponentSingleton(SomeComponent, Singleton):
            pass
        with Environment(SomeComponentSingleton):
            s1 = Environment.provide(SomeComponent, object())
            s2 = Environment.provide(SomeComponent, object())
            self.assertIs(s1, s2)
            s3 = Environment.provide(SomeComponentSingleton, object())
            self.assertIs(s1, s3)

    def test_garbage_collection(self):
        with Environment() as e:
            d = Dependent()
            _ = d.some_component
            gc.collect()
            self.assertTrue(e.has_instance(SomeComponent, d))
            del d
            check_garbage(self, e)
