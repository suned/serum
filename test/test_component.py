import unittest
from serum import Component, abstractmethod
from serum._exceptions import InvalidComponent


class ComponentTests(unittest.TestCase):
    def test_component_cant_have_init(self):
        with self.assertRaises(InvalidComponent):
            class SomeComponent(Component):
                def __init__(self):
                    pass

    def test_component_can_be_abstract(self):
        class AbstractComponent(Component):
            @abstractmethod
            def test(self):
                pass

        with self.assertRaises(TypeError):
            AbstractComponent()
