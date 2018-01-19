import unittest
from serum import immutable


class C:
    a = immutable('a')


class ImmutableTest(unittest.TestCase):
    def test_immutable_fields_are_immutable(self):
        c = C()
        with self.assertRaises(AttributeError):
            c.a = 'b'

    def test_immutable_fields_return_correct_value(self):
        c = C()
        self.assertEqual(c.a, 'a')
