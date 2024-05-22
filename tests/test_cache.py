import os
import random
import shutil
import tempfile
import unittest

from permacache import cache


def fn(x, y=2, z=3, *args):
    fn.counter += 1
    return x, y, z, args


class LockedShelfTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        cache.CACHE = self.dir.name
        fn.counter = 0
        self.f = cache.permacache("func")(fn)

    def tearDown(self):
        del self.f
        self.dir.__exit__(None, None, None)

    def test_basic(self):
        self.assertEqual(fn.counter, 0)
        self.assertEqual(self.f(1, 2, 3), (1, 2, 3, ()))
        self.assertEqual(fn.counter, 1)
        self.assertEqual(self.f(1, 2, 3), (1, 2, 3, ()))
        self.assertEqual(fn.counter, 1)
        self.assertEqual(self.f(x=1, y=2, z=3), (1, 2, 3, ()))
        self.assertEqual(fn.counter, 1)
        self.assertEqual(self.f(3, 2, 1), (3, 2, 1, ()))
        self.assertEqual(fn.counter, 2)
        self.assertEqual(self.f(3, 2, 1, 0, -1), (3, 2, 1, (0, -1)))
        self.assertEqual(fn.counter, 3)
