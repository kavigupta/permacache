import os
import random
import shutil
import tempfile
import unittest

from permacache import cache


# pylint: disable=keyword-arg-before-vararg
def fn(x, y=2, z=3, *args):
    fn.counter += 1
    return x, y, z, args


class ExportTest(unittest.TestCase):
    def test_basic_export(self):
        dir1 = tempfile.TemporaryDirectory()
        cache.CACHE = dir1.name
        zipfile = tempfile.mktemp()
        fn.counter = 0
        cache.permacache("f")(fn)(1, 2, 3)
        self.assertEqual(fn.counter, 1)
        cache.to_file("f", zipfile)
        cache.from_file("g", zipfile)
        cache.permacache("g")(fn)(1, 2, 3)
        self.assertEqual(fn.counter, 1)
        cache.permacache("h")(fn)(1, 2, 3)
        self.assertEqual(fn.counter, 2)
