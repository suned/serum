import unittest
from serum import create, Component, Environment
from serum.exceptions import NoEnvironment


class SomeComponent(Component):
    pass


class CreateTests(unittest.TestCase):
    def test_create_fails_outside_environment(self):
        with self.assertRaises(NoEnvironment):
            create(SomeComponent)

    def test_create_injects_component(self):
        with Environment():
            some_component = create(SomeComponent)
            self.assertIsInstance(some_component, SomeComponent)
