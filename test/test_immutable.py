import unittest
from serum import immutable


class ImmutableTest(unittest.TestCase):
    def test_immutable_fields_are_immutable(self):
        class C:
            a = immutable('a')
        c = C()
        with self.assertRaises(AttributeError):
            c.a = 'b'
