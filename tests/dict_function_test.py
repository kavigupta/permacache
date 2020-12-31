import unittest

from permacache.dict_function import dict_function


class LockedShelfTest(unittest.TestCase):
    def test_empty_dict_function(self):
        sig = dict()
        self.assertEqual(dict(t=2), dict_function(sig, fn)(2))
        self.assertEqual(dict(t=2, k=10), dict_function(sig, fn)(2, 10))
        self.assertEqual(dict(t=2, k=10), dict_function(sig, fn)(2, k=10))
        self.assertEqual(dict(t=2, v=10), dict_function(sig, fn)(2, v=10))

    def test_has_function(self):
        sig = dict(k=lambda x: x ** 2)
        self.assertEqual(dict(t=2), dict_function(sig, fn)(2))
        self.assertEqual(dict(t=2, k=100), dict_function(sig, fn)(2, 10))
        self.assertEqual(dict(t=2, k=100), dict_function(sig, fn)(2, k=10))
        self.assertEqual(dict(t=2, v=10), dict_function(sig, fn)(2, v=10))

    def test_has_key(self):
        sig = dict(k=None)
        self.assertEqual(dict(t=2), dict_function(sig, fn)(2))
        self.assertEqual(dict(t=2, k=None), dict_function(sig, fn)(2, 10))
        self.assertEqual(dict(t=2, k=None), dict_function(sig, fn)(2, k=10))
        self.assertEqual(dict(t=2, v=10), dict_function(sig, fn)(2, v=10))


def fn(t, k=2, v=3):
    pass
