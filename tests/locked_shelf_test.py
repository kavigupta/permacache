import json
import os
import random
import shutil
import unittest

from permacache.hash import stable_hash
from permacache.locked_shelf import IndividualFileLockedStore, LockedShelf


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

    def test_large_key(self):
        with self.shelf as s:
            s["a" * 100] = "b"
            self.assertEqual(s["a" * 100], "b")
            self.assertTrue("a" * 100 in s)
            self.assertFalse(stable_hash("a" * 100)[:20] in s)


class LockedShelfTestLargeObjects(LockedShelfTest):
    def setUp(self):
        self.shelf = LockedShelf("temp/tempshelf", allow_large_values=True)


class IndividualFileLockedStoreTest(LockedShelfTest):
    def setUp(self):
        self.shelf = IndividualFileLockedStore("temp/tempshelf")

    def test_put_and_access(self):
        super().test_put_and_access()
        self.assertEqual(os.listdir("temp/tempshelf"), [".a"])
        with open("temp/tempshelf/.a") as f:
            self.assertEqual(json.load(f), {"a": "b"})

    def test_several_accesses(self):
        super().test_several_accesses()
        for p in os.listdir("temp/tempshelf"):
            self.assertIn(p, [f".{x}" for x in range(100)])

    def test_large_key(self):
        super().test_large_key()
        h = stable_hash("a" * 100)[:20]
        self.assertEqual(os.listdir("temp/tempshelf"), [h])
        with open("temp/tempshelf/" + h) as f:
            self.assertEqual(json.load(f), {"a" * 100: "b"})
