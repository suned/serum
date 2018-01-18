import unittest
from serum import Environment, Component, abstractmethod
from serum.exceptions import InvalidDependency, UnregisteredDependency


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
        with self.assertRaises(InvalidDependency):
            Environment().use(NotAComponent)

    def test_can_register_component(self):
        e = Environment(SomeComponent)
        self.assertTrue(SomeComponent in e)
        e = Environment()
        self.assertFalse(SomeComponent in e)
        e.use(SomeComponent)
        self.assertTrue(SomeComponent in e)

    def test_environment_provides_concrete_component(self):
        with Environment():
            c = Environment.get(SomeComponent)
            self.assertIsInstance(c, SomeComponent)

    def test_environment_cant_provide_abstract_component(self):
        with Environment():
            with self.assertRaises(UnregisteredDependency):
                Environment.get(AbstractComponent)

    def test_environment_provides_concrete_subclass(self):
        with Environment(ConcreteComponent):
            c = Environment.get(AbstractComponent)
            self.assertIsInstance(c, AbstractComponent)
            self.assertIsInstance(c, ConcreteComponent)

    def test_environment_provides_correct_implementation(self):
        with Environment(ConcreteComponent):
            c = Environment.get(AbstractComponent)
            self.assertIsInstance(c, AbstractComponent)
            self.assertIsInstance(c, ConcreteComponent)
        with Environment(AlternativeComponent):
            c = Environment.get(AbstractComponent)
            self.assertIsInstance(c, AbstractComponent)
            self.assertIsInstance(c, AlternativeComponent)
