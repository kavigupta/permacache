import random
import shutil
import unittest

from permacache.locked_shelf import LockedShelf


class LockedShelfTest(unittest.TestCase):
    def setUp(self):
        self.shelf = LockedShelf("temp/tempshelf")

    def tearDown(self):
        self.shelf.close()
        shutil.rmtree("temp")

    def get_then_set(self):
        with self.shelf as s:
            self.assertFalse("anything" in s)
            s["hi"] = 3

    def test_put_and_access(self):
        with self.shelf as s:
            s["a"] = "b"
            self.assertEqual(s["a"], "b")
            self.assertTrue("a" in s)
            self.assertFalse("b" in s)

    def test_several_accesses(self):
        symbols = [str(x) for x in range(100)]
        operations = "put", "get"

        d = {}

        for _ in range(100):
            with self.shelf as s:
                op = random.choice(operations)
                if op == "put":
                    k, v = random.choice(symbols), random.choice(symbols)
                    d[k] = v
                    s[k] = v
                else:
                    k = random.choice(symbols)
                    if k in d:
                        self.assertTrue(k in s)
                        self.assertEqual(s[k], d[k])
                    else:
                        self.assertFalse(k in s)


class LockedShelfTestLargeObjects(LockedShelfTest):
    def setUp(self):
        self.shelf = LockedShelf("temp/tempshelf", allow_large_values=True)
