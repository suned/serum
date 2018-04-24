import unittest
from serum import mock, dependency, inject, Context


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


class MockTests(unittest.TestCase):
    def test_mock_always_replaces_component(self):
        with Context():
            some_component_mock = mock(SomeComponent)
            some_component_mock.method.return_value = 'some other value'
            d = Dependent()
            self.assertIs(d.some_component, some_component_mock)
            self.assertEqual(d.some_component.method(), 'some other value')

    def test_mocks_are_reset_after_context_exit(self):
        with Context():
            some_component_mock = mock(SomeComponent)
            d = Dependent()
            self.assertIs(some_component_mock, d.some_component)

        with Context():
            d = Dependent()
            self.assertIsNot(some_component_mock, d.some_component)
            self.assertIsInstance(d.some_component, SomeComponent)

    def test_mock_is_specced(self):
        with Context():
            some_component_mock = mock(SomeComponent)
            self.assertIsInstance(some_component_mock, SomeComponent)
            with self.assertRaises(AttributeError):
                some_component_mock.bad_method()
            with self.assertRaises(TypeError):
                some_component_mock()
            some_callable_component = mock(SomeCallableComponent)
            some_callable_component.return_value = 'mocked value'
            self.assertEqual(some_callable_component(), 'mocked value')

    def test_mock_replaces_named_value(self):
        class Dependency:
            def method(self):
                return 'not value'

        e = Context(key=Dependency())
        with e:
            mock_dependency = mock('key')
            mock_dependency.method.return_value = 'value'
            with self.assertRaises(AttributeError):
                mock_dependency.no_such_method()
            injected = NamedDependent().key
            self.assertEqual(injected, mock_dependency)
            self.assertEqual(mock_dependency.method(), 'value')
        with e:
            injected = NamedDependent().key
            self.assertEqual(injected.method(), 'not value')
