import os
import shutil
import random

import numpy as np
import unittest

from permacache.locked_shelf import LockedShelf


class LockedShelfTest(unittest.TestCase):
    def get_then_set_test(self):
        for _ in range(100):
            shelf1 = LockedShelf("temp/tempshelf", multiprocess_safe=True)
            shelf2 = LockedShelf("temp/tempshelf", multiprocess_safe=True)

            def set1():
                with shelf1 as f:
                    f["a"] = 2

            def set2():
                with shelf2 as f:
                    f["b"] = 3

            def close1():
                shelf1.close()

            def close2():
                shelf2.close()

            queues = [[set1, close1], [set2, close2]]
            while any(queues):
                idx = np.random.choice(len(queues))
                fn = queues[idx].pop(0)
                print(fn)
                fn()
                if not queues[idx]:
                    queues.pop(idx)
            with LockedShelf("temp/tempshelf") as f:
                self.assertEqual(f["a"], 2)
                self.assertEqual(f["b"], 3)
            shutil.rmtree("temp")
