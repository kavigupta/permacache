import os
import sys
import tempfile
import unittest

from parameterized import parameterized_class

from permacache import cache

seeds = [(seed,) for seed in range(10)] if sys.platform != "win32" else []


class GenericOutFileCacheTest(unittest.TestCase):
    def get_function(self):
        raise NotImplementedError

    def setUp(self):
        # we clean this up in tearDown
        # pylint: disable=consider-using-with
        self.outdir = tempfile.TemporaryDirectory()
        self.cachedir = tempfile.TemporaryDirectory()
        cache.CACHE = self.cachedir.name
        self.f = self.get_function()
        self.f.function.counter = 0

    def tearDown(self):
        del self.f
        self.cachedir.__exit__(None, None, None)
        self.outdir.__exit__(None, None, None)

    def out_path(self, name):
        return os.path.join(self.outdir.name, name)

    def assertCounter(self, value):
        self.assertEqual(self.f.function.counter, value)

    def assertAtPath(self, path, value):
        with open(self.out_path(path), "r") as f:
            self.assertEqual(f.read(), value)

    def writeToPath(self, path, value):
        with open(self.out_path(path), "w") as f:
            f.write(value)


def single_output(x, y=2, *, out_file):
    single_output.counter += 1
    with open(out_file, "w") as f:
        f.write(str(x * y))
    return [x, y]


single_output.counter = 0


@parameterized_class(("seed",), seeds)
class SingleOutputTest(GenericOutFileCacheTest):
    def get_function(self):
        return cache.permacache("func", out_file="out_file")(single_output)

    def test_basic(self):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertCounter(1)
        self.assertAtPath("abc", "246")

    def test_basic_overwritten(self):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertCounter(1)
        self.writeToPath("abc", "hi")
        self.assertEqual(self.f(123, out_file=self.out_path("def")), [123, 2])
        self.assertAtPath("def", "246")
        self.assertCounter(2)

    def test_can_use_first(self):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertEqual(self.f(123, out_file=self.out_path("def")), [123, 2])
        self.assertCounter(1)
        self.writeToPath("def", "hi")
        self.assertEqual(self.f(123, out_file=self.out_path("ghi")), [123, 2])
        self.assertCounter(1)
        self.assertAtPath("ghi", "246")

    def test_can_use_second(self):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertEqual(self.f(123, out_file=self.out_path("def")), [123, 2])
        self.assertCounter(1)
        self.writeToPath("abc", "hi")
        self.assertEqual(self.f(123, out_file=self.out_path("ghi")), [123, 2])
        self.assertCounter(1)
        self.assertAtPath("ghi", "246")

    def test_all_options_deleted_write_over(self):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertEqual(self.f(123, out_file=self.out_path("def")), [123, 2])
        self.assertCounter(1)
        self.writeToPath("abc", "hi")
        self.writeToPath("def", "hi")
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertCounter(2)
        self.assertAtPath("abc", "246")

    def test_all_options_deleted_write_new(self):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertEqual(self.f(123, out_file=self.out_path("def")), [123, 2])
        self.assertCounter(1)
        self.writeToPath("abc", "hi")
        self.writeToPath("def", "hi")
        self.assertEqual(self.f(123, out_file=self.out_path("ghi")), [123, 2])
        self.assertCounter(2)
        self.assertAtPath("ghi", "246")

    def test_independent_writes(self):
        self.assertCounter(0)
        self.assertEqual(self.f(123, out_file=self.out_path("abc")), [123, 2])
        self.assertEqual(self.f(234, out_file=self.out_path("def")), [234, 2])
        self.assertCounter(2)
        self.assertAtPath("abc", "246")
        self.assertAtPath("def", "468")

    def test_independent_overwrites(self):
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


def multi_output(x, y=2, *, out_file1, out_file2):
    multi_output.counter += 1
    with open(out_file1, "w") as f:
        f.write(str(x * y))
    with open(out_file2, "w") as f:
        f.write(str(x + y))
    return [x, y]


multi_output.counter = 0


@parameterized_class(("seed",), seeds)
class MultiOutputTest(GenericOutFileCacheTest):
    def get_function(self):
        return cache.permacache("func", out_file=["out_file1", "out_file2"])(
            multi_output
        )

    def test_basic(self):
        self.assertCounter(0)
        self.assertEqual(
            self.f(
                123, 2, out_file1=self.out_path("abc"), out_file2=self.out_path("def")
            ),
            [123, 2],
        )
        self.assertAtPath("abc", "246")
        self.assertAtPath("def", "125")
        self.assertCounter(1)
        self.assertEqual(
            self.f(
                123, 2, out_file1=self.out_path("aoeu"), out_file2=self.out_path("qkjx")
            ),
            [123, 2],
        )
        self.assertAtPath("aoeu", "246")
        self.assertAtPath("qkjx", "125")
        self.assertCounter(1)

    def test_basic_overwritten(self):
        self.assertCounter(0)
        self.assertEqual(
            self.f(
                123, 2, out_file1=self.out_path("abc"), out_file2=self.out_path("def")
            ),
            [123, 2],
        )
        self.assertCounter(1)
        self.writeToPath("abc", "hi")
        self.assertEqual(
            self.f(
                123, 2, out_file1=self.out_path("ghi"), out_file2=self.out_path("jkl")
            ),
            [123, 2],
        )
        self.assertAtPath("ghi", "246")
        self.assertAtPath("jkl", "125")
        self.assertCounter(2)
