from serum import mock, dependency, inject, Context

import pytest


@dependency
class SomeComponent:
    def method(self):
        return 'some value'


@dependency
class SomeCallableComponent:
    def __call__(self):
        return 'some value'


@inject
class Dependent:
    some_component: SomeComponent
    some_callable_component: SomeCallableComponent


@inject
class NamedDependent:
    key: str


def test_mock_always_replaces_component():
    with Context():
        some_component_mock = mock(SomeComponent)
        some_component_mock.method.return_value = 'some other value'
        d = Dependent()
        assert d.some_component is some_component_mock
        assert d.some_component.method() == 'some other value'


def test_mocks_are_reset_after_context_exit():
    with Context():
        some_component_mock = mock(SomeComponent)
        d = Dependent()
        assert some_component_mock is d.some_component

    with Context():
        d = Dependent()
        assert some_component_mock is not d.some_component
        assert isinstance(d.some_component, SomeComponent)


def test_mock_is_specced():
    with Context():
        some_component_mock = mock(SomeComponent)
        assert isinstance(some_component_mock, SomeComponent)
        with pytest.raises(AttributeError):
            some_component_mock.bad_method()
        with pytest.raises(TypeError):
            some_component_mock()
        some_callable_component = mock(SomeCallableComponent)
        some_callable_component.return_value = 'mocked value'
        assert some_callable_component() == 'mocked value'


def test_mock_replaces_named_value():
    class Dependency:
        def method(self):
            return 'not value'

    e = Context(key=Dependency())
    with e:
        mock_dependency = mock('key')
        mock_dependency.method.return_value = 'value'
        with pytest.raises(AttributeError):
            mock_dependency.no_such_method()
        injected = NamedDependent().key
        assert injected == mock_dependency
        assert mock_dependency.method() == 'value'
    with e:
        injected = NamedDependent().key
        assert injected.method() == 'not value'
