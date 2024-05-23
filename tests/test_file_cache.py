import os
import sys
import tempfile
import unittest

from parameterized import parameterized

from permacache import cache

def multi(f):
    if sys.platform == "win32":
        return None
    return parameterized.expand([(seed,) for seed in range(10)])(f)

def single_output(x, y=2, *, out_file):
    single_output.counter += 1
    with open(out_file, "w") as f:
        f.write(str(x * y))
    return [x, y]


class PermacacheTest(unittest.TestCase):
    def setUp(self):
        # we clean this up in tearDown
        # pylint: disable=consider-using-with
        self.outdir = tempfile.TemporaryDirectory()
        self.cachedir = tempfile.TemporaryDirectory()
        cache.CACHE = self.cachedir.name
        single_output.counter = 0
        self.f = cache.permacache("func", out="out_file")(single_output)

    def tearDown(self):
        del self.f
        self.cachedir.__exit__(None, None, None)
        self.outdir.__exit__(None, None, None)

    def out_path(self, name):
        return os.path.join(self.outdir.name, name)

    def assertCounter(self, value):
        self.assertEqual(single_output.counter, value)

    def assertAtPath(self, path, value):
        with open(self.out_path(path), "r") as f:
            self.assertEqual(f.read(), value)

    def writeToPath(self, path, value):
        with open(self.out_path(path), "w") as f:
            f.write(value)

    @multi
    def test_basic(self, _):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertCounter(1)
        self.assertAtPath("abc", "246")

    @multi
    def test_basic_overwritten(self, _):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertCounter(1)
        self.writeToPath("abc", "hi")
        self.assertEqual(self.f(123, out_file=self.out_path("def")), [123, 2])
        self.assertAtPath("def", "246")
        self.assertCounter(2)

    @multi
    def test_can_use_first(self, _):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertEqual(self.f(123, out_file=self.out_path("def")), [123, 2])
        self.assertCounter(1)
        self.writeToPath("def", "hi")
        self.assertEqual(self.f(123, out_file=self.out_path("ghi")), [123, 2])
        self.assertCounter(1)
        self.assertAtPath("ghi", "246")

    @multi
    def test_can_use_second(self, _):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertEqual(self.f(123, out_file=self.out_path("def")), [123, 2])
        self.assertCounter(1)
        self.writeToPath("abc", "hi")
        self.assertEqual(self.f(123, out_file=self.out_path("ghi")), [123, 2])
        self.assertCounter(1)
        self.assertAtPath("ghi", "246")

    @multi
    def test_all_options_deleted_write_over(self, _):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertEqual(self.f(123, out_file=self.out_path("def")), [123, 2])
        self.assertCounter(1)
        self.writeToPath("abc", "hi")
        self.writeToPath("def", "hi")
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertCounter(2)
        self.assertAtPath("abc", "246")

    @multi
    def test_all_options_deleted_write_new(self, _):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertEqual(self.f(123, out_file=self.out_path("def")), [123, 2])
        self.assertCounter(1)
        self.writeToPath("abc", "hi")
        self.writeToPath("def", "hi")
        self.assertEqual(self.f(123, out_file=self.out_path("ghi")), [123, 2])
        self.assertCounter(2)
        self.assertAtPath("ghi", "246")

    @multi
    def test_independent_writes(self, _):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertEqual(self.f(234, out_file=self.out_path("def")), [234, 2])
        self.assertCounter(2)
        self.assertAtPath("abc", "246")
        self.assertAtPath("def", "468")

    @multi
    def test_independent_overwrites(self, _):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertEqual(self.f(234, out_file=self.out_path("def")), [234, 2])
        self.assertCounter(2)
        self.assertAtPath("abc", "246")
        self.assertAtPath("def", "468")
        self.assertEqual(self.f(123, out_file=self.out_path("def")), [123, 2])
        self.assertAtPath("def", "246")
        self.assertCounter(2)
        self.assertEqual(self.f(234, out_file=self.out_path("abc")), [234, 2])
        self.assertCounter(3)
        self.assertAtPath("abc", "468")
