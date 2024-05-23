import shutil
import threading
import time
import unittest

import numpy as np
from parameterized import parameterized

from permacache.locked_shelf import LockedShelf


class LockedShelfTest(unittest.TestCase):
    @parameterized.expand([(seed,) for seed in range(100)])
    def test_get_then_set(self, seed):
        def thread(key, value, seed):
            shelf = LockedShelf("temp/tempshelf", multiprocess_safe=True)
            rng = np.random.RandomState(seed)

            def maybe_sleep():
                if rng.rand() < 0.5:
                    time.sleep(rng.rand() * 0.1)

            with shelf as f:
                maybe_sleep()
                f[key] = value

            maybe_sleep()
            shelf.close()

        threads = [
            threading.Thread(target=thread, args=("a", 2, seed)),
            threading.Thread(target=thread, args=("b", 3, seed + 1000)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        with LockedShelf("temp/tempshelf") as f:
            self.assertEqual(f["a"], 2)
            self.assertEqual(f["b"], 3)

    def tearDown(self):
        try:
            shutil.rmtree("temp")
        except FileNotFoundError:
            pass
