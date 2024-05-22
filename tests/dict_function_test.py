import unittest

from permacache.dict_function import dict_function, drop_if_equal, parallel_output


class DictFunctionTest(unittest.TestCase):
    def test_empty_dict_function(self):
        sig = dict()
        self.assertEqual(dict(t=2, k=2, v=3), dict_function(sig, fn)([2], dict()))
        self.assertEqual(dict(t=2, k=10, v=3), dict_function(sig, fn)([2, 10], dict()))
        self.assertEqual(dict(t=2, k=10, v=3), dict_function(sig, fn)([2], dict(k=10)))
        self.assertEqual(dict(t=2, v=10, k=2), dict_function(sig, fn)([2], dict(v=10)))

    def test_has_function(self):
        sig = dict(k=lambda x: x**2)
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

    def test_parallel(self):
        sig = dict(t=lambda t: t**2, k=str)
        self.assertEqual(
            parallel_output(
                [dict(t=4, k="2", v=3), dict(t=9, k="2", v=3), dict(t=16, k="2", v=3)]
            ),
            dict_function(sig, fn)([[2, 3, 4]], dict(), parallel="t"),
        )

        sig = dict(k=str)
        self.assertEqual(
            parallel_output(
                [dict(t=2, k="2", v=3), dict(t=3, k="2", v=3), dict(t=4, k="2", v=3)]
            ),
            dict_function(sig, fn)([[2, 3, 4]], dict(), parallel="t"),
        )

    def test_parallel_multi(self):
        sig = dict(t=lambda t: t**2)
        self.assertEqual(
            parallel_output(
                [dict(t=4, k="a", v=3), dict(t=9, k="b", v=3), dict(t=16, k="c", v=3)]
            ),
            dict_function(sig, fn)([[2, 3, 4], "abc"], dict(), parallel=("t", "k")),
        )

        with self.assertRaises(ValueError) as context:
            dict_function(sig, fn)([[2, 3, 4], "abcd"], dict(), parallel=("t", "k"))
        self.assertEqual("Incompatible lengths: 3, 4", str(context.exception))


def fn(t, k=2, v=3):
    del t, k, v
