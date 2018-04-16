import unittest
from abc import abstractmethod, ABC

from serum import (
    inject,
    dependency,
    Environment
)
from serum._injected_dependency import Dependency as InjectedDependency
from serum.exceptions import NoNamedDependency, InjectionError


@dependency
class SomeDependency:
    pass


@dependency
class AbstractDependency(ABC):
    @abstractmethod
    def abstract(self):
        pass


class ConcreteDependency(AbstractDependency):
    def abstract(self):
        pass


class AlternativeDependency(AbstractDependency):
    def abstract(self):
        pass


@dependency
@inject
class Chain:
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
    key: str


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
    def test_inject_string(self, key: str):
        self.assertEqual(key, 'value')

    def test_static_dependency(self):
        self.assertIsInstance(Dependent.some_dependency, InjectedDependency)

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

    def test_overriding_injected_parameters(self):
        @inject
        def f(first, second):
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

    def test_override_class_dependency(self):
        self.assertEqual(
            Dependent(some_dependency='test').some_dependency,
            'test'
        )

    def test_invalid_class_dependencies(self):
        @dependency
        class BadDependency:
            def __init__(self, a):
                pass

        @inject
        class D:
            _: BadDependency
        with self.assertRaises(InjectionError):
            _ = D()._

    def test_subtype_is_bad_dependency(self):
        @dependency
        class D:
            pass

        class BadDependency(D):
            def __init__(self, a):
                pass

        @inject
        class C:
            _: D

        with Environment(BadDependency):
            with self.assertRaises(InjectionError):
                _ = C()._

    def test_dependency_raises_type_error(self):
        @dependency
        class BadDependency:
            def __init__(self):
                raise TypeError()

        @inject
        class C:
            _: BadDependency

        with self.assertRaises(InjectionError):
            _ = C()._

    def test_no_named_dependency(self):
        @inject
        class C:
            name: str

        with self.assertRaises(NoNamedDependency):
            _ = C().name

    def test_no_dependencies(self):
        @inject
        class C:
            pass

        self.assertIsInstance(C(), C)

    def test_missing_init_dependencies(self):
        class D:
            @inject
            def __init__(self, a):
                pass

        @inject
        class C:
            d: D

        with self.assertRaises(NoNamedDependency):
            _ = C().d

    def test_inject_with_set_attr_override(self):
        @dependency
        class D:
            pass

        @inject
        class C:
            d: D

            def __setattr__(self, key, value):
                raise AttributeError()

        with self.assertRaises(InjectionError):
            _ = C().d

    def test_dependency_error_in_function(self):
        @dependency
        class D:
            def __init__(self):
                raise Exception()

        @inject
        def f(d: D):
            pass

        with self.assertRaises(InjectionError):
            f()

    def test_dependency_subtype_error_in_function(self):
        @dependency
        class D:
            pass

        class D2(D):
            def __init__(self):
                raise Exception()

        @inject
        def f(d: D):
            pass

        with Environment(D2):
            with self.assertRaises(InjectionError):
                f()

    def test_inject_with_no_annotations(self):
        @inject
        def f(a):
            return a

        with Environment(a='a'):
            self.assertEqual(f(), 'a')

        with self.assertRaises(TypeError):
            f()

    def test_dependency_provided_as_keyword_arg(self):
        @inject
        def f(a):
            return a

        self.assertEqual(f('a'), 'a')



