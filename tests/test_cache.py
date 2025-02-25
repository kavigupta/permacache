import os
import shutil
import tempfile
import unittest

from permacache import cache, no_cache_global
from permacache.hash import stable_hash
from permacache.swap_unpickler import (
    renamed_symbol_unpickler,
    swap_unpickler_context_manager,
)

from .test_module.a import X as a_X
from .test_module.a import Y as a_Y
from .test_module.b import X as b_X


# pylint: disable=keyword-arg-before-vararg
def fn(x, y=2, z=3, *args):
    fn.counter += 1
    return x, y, z, args


class PermacacheTest(unittest.TestCase):

    def create_cache_fn(self):
        return cache.permacache("func")(fn)

    def setUp(self):
        # we clean this up in tearDown
        # pylint: disable=consider-using-with
        self.dir = tempfile.TemporaryDirectory()
        cache.CACHE = self.dir.name
        fn.counter = 0
        self.f = self.create_cache_fn()

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

    def test_basic_with_disabled_cache(self):
        self.assertEqual(fn.counter, 0)
        self.assertEqual(self.f(1, 2, 3), (1, 2, 3, ()))
        self.assertEqual(fn.counter, 1)
        self.assertEqual(self.f(1, 2, 3), (1, 2, 3, ()))
        self.assertEqual(fn.counter, 1)
        with no_cache_global():
            self.assertEqual(self.f(1, 2, 3), (1, 2, 3, ()))
        self.assertEqual(fn.counter, 2)


class PermacacheIndividualTest(PermacacheTest):

    def create_cache_fn(self):
        return cache.permacache("func", shelf_type="individual-file")(fn)


class PermacacheIndividualTestLocal(PermacacheTest):

    def create_cache_fn(self):
        self.local_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "test_cache", "func"
        )
        return cache.permacache(self.local_path, shelf_type="individual-file")(fn)

    def test_basic(self):
        super().test_basic()
        self.assertTrue(os.path.exists(self.local_path))
        self.assertEqual(
            set(
                os.path.join(directory, filename)
                for directory, _, filenames in os.walk(self.local_path)
                for filename in filenames
            ),
            set(
                os.path.join(self.local_path, x)
                for x in [
                    stable_hash('{"args": [], "x": 1, "y": 2, "z": 3}')[:20] + ".pkl",
                    stable_hash('{"args": [], "x": 3, "y": 2, "z": 1}')[:20] + ".pkl",
                    stable_hash('{"args": [0, -1], "x": 3, "y": 2, "z": 1}')[:20]
                    + ".pkl",
                ]
            ),
        )

    def tearDown(self):
        shutil.rmtree(self.local_path)
        return super().tearDown()


def g(x):
    g.counter += 1
    return a_X(x)


class PermacacheRemappingTest(unittest.TestCase):
    def setUp(self):
        # we clean this up in tearDown
        # pylint: disable=consider-using-with
        self.dir = tempfile.TemporaryDirectory()
        cache.CACHE = self.dir.name
        g.counter = 0
        self.f = cache.permacache("g")(g)
        self.assertIsInstance(self.f(1), a_X)
        self.assertEqual(g.counter, 1)

    def tearDown(self):
        self.dir.__exit__(None, None, None)

    def test_swap_to_b(self):
        # populate cache
        # swap to b
        self.f = cache.permacache(
            "g",
            read_from_shelf_context_manager=swap_unpickler_context_manager(
                renamed_symbol_unpickler(
                    {
                        (
                            "tests.test_module.a",
                            "X",
                        ): b_X
                    }
                )
            ),
        )(g)
        self.assertIsInstance(self.f(1), b_X)
        self.assertEqual(g.counter, 1)

    def test_swap_to_y(self):
        # populate cache
        # swap to y
        self.f = cache.permacache(
            "g",
            read_from_shelf_context_manager=swap_unpickler_context_manager(
                renamed_symbol_unpickler(
                    {
                        (
                            "tests.test_module.a",
                            "X",
                        ): a_Y
                    }
                )
            ),
        )(g)
        self.assertIsInstance(self.f(1), a_Y)
        self.assertEqual(g.counter, 1)

    def test_use_name(self):
        # populate cache
        # swap to y
        self.f = cache.permacache(
            "g",
            read_from_shelf_context_manager=swap_unpickler_context_manager(
                renamed_symbol_unpickler(
                    {
                        (
                            "tests.test_module.a",
                            "X",
                        ): ("tests.test_module.a", "Y")
                    }
                )
            ),
        )(g)
        self.assertIsInstance(self.f(1), a_Y)
        self.assertEqual(g.counter, 1)
