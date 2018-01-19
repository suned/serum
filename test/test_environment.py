import unittest

from serum import Environment, Component, abstractmethod
from serum._exceptions import InvalidDependency, UnregisteredDependency, \
    NoEnvironment, AmbiguousDependencies
import threading


class SomeComponent(Component):
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


class EnvironmentTests(unittest.TestCase):
    def test_cant_register_non_component(self):
        class NotAComponent:
            pass
        with self.assertRaises(InvalidDependency):
            Environment(NotAComponent)

    def test_can_register_component(self):
        e = Environment(SomeComponent)
        self.assertTrue(SomeComponent in e)

    def test_environment_provides_concrete_component(self):
        with Environment():
            c = Environment.provide(SomeComponent)
            self.assertIsInstance(c, SomeComponent)

    def test_environment_cant_provide_abstract_component(self):
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
        def test():
            with self.assertRaises(NoEnvironment):
                Environment.provide(AbstractComponent)

        with Environment(ConcreteComponent):
            threading.Thread(target=test).start()

    def test_nested_environments(self):
        with Environment(ConcreteComponent):
            c = Environment.provide(AbstractComponent)
            self.assertIsInstance(c, ConcreteComponent)
            with Environment(AlternativeComponent):
                c = Environment.provide(AbstractComponent)
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
            c = Environment.provide(AbstractComponent)
            self.assertIsInstance(c, ConcreteComponentSub)

    def test_fails_with_ambiguous_dependencies(self):
        with Environment(ConcreteComponent, AlternativeComponent):
            with self.assertRaises(AmbiguousDependencies):
                Environment.provide(AbstractComponent)

