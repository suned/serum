import unittest
from serum import Component, abstractmethod
from serum.exceptions import InvalidComponent


class ComponentTests(unittest.TestCase):
    def test_component_init_only_one_parameter(self):
        class SomeComponent(Component):
            def __init__(self):
                pass

        with self.assertRaises(InvalidComponent):
            class SomeComponent(Component):
                def __init__(self, a):
                    pass

    def test_component_can_be_abstract(self):
        class AbstractComponent(Component):
            @abstractmethod
            def test(self):
                pass

        with self.assertRaises(TypeError):
            AbstractComponent()
