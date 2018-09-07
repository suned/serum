from abc import abstractmethod, ABC

from serum import (
    inject,
    dependency,
    Context,
    singleton)
from serum._injected_dependency import Dependency as InjectedDependency
from serum.exceptions import NoNamedDependency, InjectionError
import pytest


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


@singleton
class SomeSingleton:
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


class SubSubDependent(SubDependent):
    pass


@inject
class OverwriteDependent(AbstractDependent):
    abstract_dependency: AlternativeDependency


@inject
class NamedDependent:
    key: str


def test_inject_gets_concrete_component():
    d = Dependent()
    assert isinstance(d.some_dependency, SomeDependency)


def test_injected_component_is_immutable():
    d = Dependent()
    with pytest.raises(AttributeError):
        d.some_dependency = 'test'


def test_inject_string():
    @Context(k='value')
    @inject
    def f(k):
        assert k == 'value'
    f()


def test_static_dependency():
    assert isinstance(Dependent.some_dependency, InjectedDependency)


def test_inject_can_get_concrete_component():
    with Context(ConcreteDependency):
        d = AbstractDependent()
        assert isinstance(d.abstract_dependency, AbstractDependency)
        assert isinstance(d.abstract_dependency, ConcreteDependency)


def test_inject_provides_correct_implementation():
    with Context(ConcreteDependency):
        d = AbstractDependent()
        assert isinstance(d.abstract_dependency, AbstractDependency)
        assert isinstance(d.abstract_dependency, ConcreteDependency)
    with Context(AlternativeDependency):
        d = AbstractDependent()
        assert isinstance(d.abstract_dependency, AbstractDependency)
        assert isinstance(d.abstract_dependency, AlternativeDependency)


def test_injection_chaining():
    d = Dependent()
    assert isinstance(d.chain, Chain)
    assert isinstance(d.chain.some_component, SomeDependency)


def test_injected_are_different_instances():
    with Context():
        d1 = Dependent()
        d2 = Dependent()
        assert d1.some_dependency is not d2.some_dependency


def test_named_dependency():
    with Context(key='value'):
        assert NamedDependent().key == 'value'


@Context(ConcreteDependency)
def test_inheritance():
    assert isinstance(
        SubDependent().abstract_dependency,
        ConcreteDependency
    )
    assert isinstance(
        OverwriteDependent().abstract_dependency,
        AlternativeDependency
    )
    assert isinstance(
        SubSubDependent().abstract_dependency,
        ConcreteDependency
    )


def test_decorate_class_with_no_annotations():
    class NoAnnotations:
        pass

    decorated = inject(NoAnnotations)
    assert decorated is NoAnnotations


def test_decorate_class_with_no_dependency_annotations():
    class NoDependencyAnnotations:
        a: int

    decorated = inject(NoDependencyAnnotations)
    assert decorated is NoDependencyAnnotations


def test_decorate_nonclass_or_nonfunction():
    result = inject(1)
    assert result == 1


def test_inject_function_dependency():
    @inject
    def f(d: SomeDependency):
        assert isinstance(d, SomeDependency)

    f()


def test_inject_function_with_non_dependency_annotations():
    @inject
    def f(a: int):
        return a

    result = f(1)
    assert result == 1


def test_overriding_injected_parameters():
    @inject
    def f(first, second):
        return first, second

    a, b = f('a', 'b')
    assert a == 'a'
    assert b == 'b'


def test_decorate_function_with_no_injected_params():
    @inject
    def f(value: int):
        return value

    with pytest.raises(TypeError):
        f()


def test_override_class_dependency():
    assert Dependent(some_dependency='test').some_dependency == 'test'


def test_invalid_class_dependencies():
    @dependency
    class BadDependency:
        def __init__(self, a):
            pass

    @inject
    class D:
        _: BadDependency

    pytest.raises(InjectionError, lambda: D()._)


def test_subtype_is_bad_dependency():
    @dependency
    class D:
        pass

    class BadDependency(D):
        def __init__(self, a):
            pass

    @inject
    class C:
        _: D

    with Context(BadDependency):
        pytest.raises(InjectionError, lambda: C()._)


def test_dependency_raises_type_error():
    @dependency
    class BadDependency:
        def __init__(self):
            raise TypeError()

    @inject
    class C:
        _: BadDependency

    pytest.raises(InjectionError, lambda: C()._)


def test_no_named_dependency():
    @inject
    class C:
        name: str

    pytest.raises(NoNamedDependency, lambda: C().name)


def test_no_dependencies():
    @inject
    class C:
        pass

    assert isinstance(C(), C)


def test_missing_init_dependencies():
    class D:
        @inject
        def __init__(self, a):
            pass

    @inject
    class C:
        d: D

    pytest.raises(NoNamedDependency, lambda: C().d)


def test_inject_with_set_attr_override():
    @dependency
    class D:
        pass

    @inject
    class C:
        d: D

        def __setattr__(self, key, value):
            raise AttributeError()

    pytest.raises(InjectionError, lambda: C().d)


def test_dependency_error_in_function():
    @dependency
    class D:
        def __init__(self):
            raise Exception()

    @inject
    def f(d: D):
        pass

    with pytest.raises(InjectionError):
        f()


def test_dependency_subtype_error_in_function():
    @dependency
    class D:
        pass

    class D2(D):
        def __init__(self):
            raise Exception()

    @inject
    def f(d: D):
        pass

    with Context(D2):
        with pytest.raises(InjectionError):
            f()


def test_inject_with_no_annotations():
    @inject
    def f(a):
        return a

    with Context(a='a'):
        assert f() == 'a'

    with pytest.raises(TypeError):
        f()


def test_dependency_provided_as_keyword_arg():
    @inject
    def f(a):
        return a

    assert f('a') == 'a'


def test_inject_with_return_annotation():
    @inject
    def f(a: int) -> int:
        return a

    with Context(a=1):
        assert f() == 1


def test_inject_singleton_without_context():
    Context._set_current_env(None)

    @inject
    class C:
        instance: SomeSingleton

    assert C().instance is C().instance
