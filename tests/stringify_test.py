import unittest
import json

import numpy as np
import torch

from permacache import stringify, stable_hash


class StringifyTest(unittest.TestCase):
    data = np.random.RandomState(0).randn(1000)
    slow_hash = "16469cff96525e3e190758d793e61f9d798cb87617787bc1312cf7a8b59aa4b2"
    fast_hash = "c97fda7d817a32aad65ce77f5043a51410c5893e6bab8e746a23f68c8e483774"

    def test_stringify_json(self):
        self.assertEqual("2", stringify(2))
        self.assertEqual("[2, 3]", stringify([2, 3]))
        self.assertEqual('{"a": 3}', stringify({"a": 3}))

    def test_stringify_attrs(self):
        import attr

        @attr.s
        class X:
            y = attr.ib()

        self.assertEqual(
            json.dumps({".attr.__name__": "X", "y": "hello"}), stringify(X("hello"))
        )

    def test_stringify_numpy(self):
        self.assertEqual(
            self.slow_hash,
            stable_hash(self.data, fast_bytes=False),
        )
        self.assertEqual(self.fast_hash, stable_hash(self.data))

    def test_stringify_torch(self):
        self.assertEqual(
            self.slow_hash,
            stable_hash(torch.tensor(self.data), fast_bytes=False),
        )
        self.assertEqual(
            self.fast_hash,
            stable_hash(torch.tensor(self.data)),
        )
