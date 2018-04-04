import unittest
from serum import Dependency, abstractmethod, inject, Key
from serum.exceptions import InvalidDependency


class DependencyTests(unittest.TestCase):
    def test_dependency_init_without_decorator(self):
        class SomeComponent(Dependency):
            def __init__(self):
                pass

        with self.assertRaises(InvalidDependency):
            class SomeComponent(Dependency):
                def __init__(self, a):
                    pass

    def test_dependency_init_without_annotation(self):
        with self.assertRaises(InvalidDependency):
            class SomeComponent(Dependency):
                @inject
                def __init__(self, a):
                    pass

    def test_dependency_init_with_annotation(self):
        class SomeComponent(Dependency):
            @inject
            def __init__(self, a: Key('test')):
                pass

    def test_dependency_init_with_some_annotations(self):
        with self.assertRaises(InvalidDependency):
            class SomeComponent(Dependency):
                @inject
                def __init__(self, a, b: Key('test')):
                    pass

    def test_dependency_can_be_abstract(self):
        class AbstractComponent(Dependency):
            @abstractmethod
            def test(self):
                pass

        with self.assertRaises(TypeError):
            AbstractComponent()
