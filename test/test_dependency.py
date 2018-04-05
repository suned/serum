import unittest
from typing import Sequence

from serum import Dependency, abstractmethod, inject, Name
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
            def __init__(self, a: Name):
                pass

    def test_dependency_init_with_some_annotations(self):
        with self.assertRaises(InvalidDependency):
            class SomeComponent(Dependency):
                @inject
                def __init__(self, a, b: Name):
                    pass

    def test_dependency_can_be_abstract(self):
        class AbstractComponent(Dependency):
            @abstractmethod
            def test(self):
                pass

        with self.assertRaises(TypeError):
            AbstractComponent()

    def test_dependency_can_be_generic(self):
        class AbstractComponent(Dependency, Sequence[int]):
            pass

        with self.assertRaises(TypeError):
            AbstractComponent()
