import unittest

from permacache.dict_function import dict_function, drop_if_equal


class DictFunctionTest(unittest.TestCase):
    def test_empty_dict_function(self):
        sig = dict()
        self.assertEqual(dict(t=2, k=2, v=3), dict_function(sig, fn)([2], dict()))
        self.assertEqual(dict(t=2, k=10, v=3), dict_function(sig, fn)([2, 10], dict()))
        self.assertEqual(dict(t=2, k=10, v=3), dict_function(sig, fn)([2], dict(k=10)))
        self.assertEqual(dict(t=2, v=10, k=2), dict_function(sig, fn)([2], dict(v=10)))

    def test_has_function(self):
        sig = dict(k=lambda x: x ** 2)
        self.assertEqual(dict(t=2, k=4, v=3), dict_function(sig, fn)([2], dict()))
        self.assertEqual(dict(t=2, k=100, v=3), dict_function(sig, fn)([2, 10], dict()))
        self.assertEqual(dict(t=2, k=100, v=3), dict_function(sig, fn)([2], dict(k=10)))
        self.assertEqual(dict(t=2, v=10, k=4), dict_function(sig, fn)([2], dict(v=10)))

    def test_has_key(self):
        sig = dict(k=None)
        self.assertEqual(dict(t=2, k=None, v=3), dict_function(sig, fn)([2], dict()))
        self.assertEqual(
            dict(t=2, k=None, v=3), dict_function(sig, fn)([2, 10], dict())
        )
        self.assertEqual(
            dict(t=2, k=None, v=3), dict_function(sig, fn)([2], dict(k=10))
        )
        self.assertEqual(
            dict(t=2, v=10, k=None), dict_function(sig, fn)([2], dict(v=10))
        )

    def test_drop_if(self):
        sig = dict(k=drop_if_equal(2), v=drop_if_equal(10))
        self.assertEqual(dict(t=2, v=3), dict_function(sig, fn)([2], dict()))
        self.assertEqual(dict(t=2, k=10, v=3), dict_function(sig, fn)([2, 10], dict()))
        self.assertEqual(dict(t=2, k=10, v=3), dict_function(sig, fn)([2], dict(k=10)))
        self.assertEqual(dict(t=2), dict_function(sig, fn)([2], dict(v=10)))


def fn(t, k=2, v=3):
    pass
