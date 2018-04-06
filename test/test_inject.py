import unittest

from typing import Union

from serum import inject, Dependency, Environment, abstractmethod, Name, \
    NamedDependency
from serum._injected_dependency import Dependency as InjectedDependency
from serum.exceptions import UnregisteredDependency


class SomeDependency(Dependency):
    pass


class AbstractDependency(Dependency):
    @abstractmethod
    def abstract(self):
        pass


class ConcreteDependency(AbstractDependency):
    def abstract(self):
        pass


class AlternativeDependency(AbstractDependency):
    def abstract(self):
        pass


@inject
class Chain(Dependency):
    some_component: SomeDependency


@inject
class Dependent:
    some_dependency: SomeDependency
    chain: Chain


@inject
class AbstractDependent:
    abstract_dependency: AbstractDependency


class SubDependent(AbstractDependent):
    pass


@inject
class OverwriteDependent(AbstractDependent):
    abstract_dependency: AlternativeDependency


@inject
class NamedDependent:
    key: Name[str]


class InjectTests(unittest.TestCase):

    def test_inject_gets_concrete_component(self):
        d = Dependent()
        self.assertIsInstance(d.some_dependency, SomeDependency)

    def test_injected_component_is_immutable(self):
        d = Dependent()
        with self.assertRaises(AttributeError):
            d.some_dependency = 'test'

    @Environment(key='value')
    @inject
    def test_inject_string(self, key: Name[str]):
        self.assertEqual(key, 'value')

    def test_static_dependency(self):
        self.assertIsInstance(Dependent.some_dependency, InjectedDependency)

    def test_inject_cant_get_abstract_component(self):
        with Environment():
            with self.assertRaises(UnregisteredDependency):
                AbstractDependent()

    def test_inject_can_get_concrete_component(self):
        with Environment(ConcreteDependency):
            d = AbstractDependent()
            self.assertIsInstance(d.abstract_dependency, AbstractDependency)
            self.assertIsInstance(d.abstract_dependency, ConcreteDependency)

    def test_inject_provides_correct_implementation(self):
        with Environment(ConcreteDependency):
            d = AbstractDependent()
            self.assertIsInstance(d.abstract_dependency, AbstractDependency)
            self.assertIsInstance(d.abstract_dependency, ConcreteDependency)
        with Environment(AlternativeDependency):
            d = AbstractDependent()
            self.assertIsInstance(d.abstract_dependency, AbstractDependency)
            self.assertIsInstance(d.abstract_dependency, AlternativeDependency)

    def test_injection_chaining(self):
        d = Dependent()
        self.assertIsInstance(d.chain, Chain)
        self.assertIsInstance(d.chain.some_component, SomeDependency)

    def test_injected_are_different_instances(self):
        with Environment():
            d1 = Dependent()
            d2 = Dependent()
            self.assertIsNot(d1.some_dependency, d2.some_dependency)

    def test_named_dependency(self):
        with Environment(key='value'):
            self.assertEqual(NamedDependent().key, 'value')

    @Environment(ConcreteDependency)
    def test_inheritance(self):
        self.assertIsInstance(
            SubDependent().abstract_dependency,
            ConcreteDependency
        )
        self.assertIsInstance(
            OverwriteDependent().abstract_dependency,
            AlternativeDependency
        )

    def test_decorate_class_with_no_annotations(self):
        class NoAnnotations:
            pass
        decorated = inject(NoAnnotations)
        self.assertIs(decorated, NoAnnotations)

    def test_decorate_class_with_no_dependency_annotations(self):
        class NoDependencyAnnotations:
            a: int
        decorated = inject(NoDependencyAnnotations)
        self.assertIs(decorated, NoDependencyAnnotations)

    def test_decorate_nonclass_or_nonfunction(self):
        result = inject(1)
        self.assertEqual(result, 1)

    @inject
    def test_inject_function_dependency(self, dependency: SomeDependency):
        self.assertIsInstance(dependency, SomeDependency)

    def test_inject_function_with_non_dependency_annotations(self):
        @inject
        def f(a: int):
            return a

        result = f(1)
        self.assertEqual(result, 1)

    @Environment(key='value')
    @inject
    def test_named_dependency_workaround(self, key: Union[NamedDependency, str]):
        self.assertEqual(key, 'value')

    def test_overriding_injected_parameters(self):
        @inject
        def f(first: Name, second: Name):
            return first, second

        a, b = f('a', 'b')
        self.assertEqual(a, 'a')
        self.assertEqual(b, 'b')

    def test_decorate_function_with_no_injected_params(self):
        @inject
        def f(value: int):
            return value

        with self.assertRaises(TypeError):
            f()

