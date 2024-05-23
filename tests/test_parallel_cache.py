import os
import random
import shutil
import tempfile
import unittest

from permacache import cache


def fn(xs, ys):
    fn.counter += len(xs)
    return [(x, ys) for x in xs]


class ParallelCacheTestNonFullyParallel(unittest.TestCase):
    def setUp(self):
        # we clean this up in tearDown
        # pylint: disable=consider-using-with
        self.dir = tempfile.TemporaryDirectory()
        cache.CACHE = self.dir.name
        fn.counter = 0
        self.f = cache.permacache("func", key_function=dict(xs=abs), parallel=["xs"])(
            fn
        )

    def tearDown(self):
        del self.f
        self.dir.__exit__(None, None, None)

    def test_basic(self):
        self.assertEqual(fn.counter, 0)
        self.assertEqual(self.f([1, 2, 3], "abc"), [(1, "abc"), (2, "abc"), (3, "abc")])
        self.assertEqual(fn.counter, 3)
        self.assertEqual(
            self.f([1, 5, 3, 1, 5], "abc"),
            [(1, "abc"), (5, "abc"), (3, "abc"), (1, "abc"), (5, "abc")],
        )
        self.assertEqual(fn.counter, 4)

        self.assertEqual(
            self.f(range(10, 20), "abc"),
            [(c, "abc") for c in range(10, 20)],
        )
        self.assertEqual(fn.counter, 14)


def fn_2(xs, ys):
    fn_2.counter += len(xs)
    return list(zip(xs, ys))


class ParallelCacheTestFullyParallel(unittest.TestCase):
    def setUp(self):
        # we clean this up in tearDown
        # pylint: disable=consider-using-with
        self.dir = tempfile.TemporaryDirectory()
        cache.CACHE = self.dir.name
        fn_2.counter = 0
        self.f = cache.permacache(
            "func", key_function=dict(xs=abs), parallel=["xs", "ys"]
        )(fn_2)

    def tearDown(self):
        del self.f
        self.dir.__exit__(None, None, None)

    def test_basic(self):
        self.assertEqual(fn_2.counter, 0)
        self.assertEqual(self.f([1, 2, 3], "abc"), [(1, "a"), (2, "b"), (3, "c")])
        self.assertEqual(fn_2.counter, 3)
        self.assertEqual(
            self.f([1, 5, 3, 1, 5], "abcde"),
            [(1, "a"), (5, "b"), (3, "c"), (1, "d"), (5, "e")],
        )
        self.assertEqual(fn_2.counter, 6)

        self.assertEqual(
            self.f(range(10, 20), range(10, 20)),
            [(c, c) for c in range(10, 20)],
        )
        self.assertEqual(fn_2.counter, 16)
