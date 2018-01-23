import unittest
from serum import inject, Component, Environment, abstractmethod
from serum.exceptions import NoEnvironment, UnregisteredDependency, \
    InvalidDependency


class SomeComponent(Component):
    pass


class AbstractComponent(Component):
    @abstractmethod
    def abstract(self):
        pass


class ConcreteComponent(AbstractComponent):
    def abstract(self):
        pass


class AlternativeComponent(AbstractComponent):
    def abstract(self):
        pass


class Chain(Component):
    some_component = inject(SomeComponent)


class Dependent:
    some_component = inject(SomeComponent)
    abstract_component = inject(AbstractComponent)
    chain = inject(Chain)


class InjectTests(unittest.TestCase):
    def test_inject_fails_outside_environment(self):
        d = Dependent()
        with self.assertRaises(NoEnvironment):
            _ = d.some_component

    def test_inject_gets_concrete_component(self):
        with Environment():
            d = Dependent()
            self.assertIsInstance(d.some_component, SomeComponent)

    def test_injected_component_is_immutable(self):
        d = Dependent()
        with Environment():
            with self.assertRaises(AttributeError):
                d.some_component = 'test'

    def test_inject_cant_get_abstract_component(self):
        d = Dependent()
        with Environment():
            with self.assertRaises(UnregisteredDependency):
                _ = d.abstract_component

    def test_inject_can_get_concrete_component(self):
        d = Dependent()
        with Environment(ConcreteComponent):
            self.assertIsInstance(d.abstract_component, AbstractComponent)
            self.assertIsInstance(d.abstract_component, ConcreteComponent)

    def test_inject_provides_correct_implementation(self):
        d = Dependent()
        with Environment(ConcreteComponent):
            self.assertIsInstance(d.abstract_component, AbstractComponent)
            self.assertIsInstance(d.abstract_component, ConcreteComponent)
        with Environment(AlternativeComponent):
            self.assertIsInstance(d.abstract_component, AbstractComponent)
            self.assertIsInstance(d.abstract_component, AlternativeComponent)

    def test_injection_chaining(self):
        d = Dependent()
        with Environment():
            self.assertIsInstance(d.chain, Chain)
            self.assertIsInstance(d.chain.some_component, SomeComponent)

    def test_inject_non_component_fails(self):
        class Test:
            pass
        with self.assertRaises(InvalidDependency):
            inject(Test)

    def test_injected_is_always_same_instance(self):
        with Environment():
            d1 = Dependent()
            self.assertIs(d1.some_component, d1.some_component)

    def test_injected_are_different_instances(self):
        with Environment():
            d1 = Dependent()
            d2 = Dependent()
            self.assertIsNot(d1.some_component, d2.some_component)
