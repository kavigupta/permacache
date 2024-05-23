import json
import sys
import unittest

import numpy as np
import pandas as pd
import torch

from permacache import stable_hash, stringify


class StringifyTest(unittest.TestCase):
    data = np.random.RandomState(0).randn(1000)
    slow_hash = {
        "linux": "16469cff96525e3e190758d793e61f9d798cb87617787bc1312cf7a8b59aa4b2",
        "win32": "faaa45dfa377870db4d547ca91187566b6b74983adaf16241a80ef96af592285",
        "darwin": "97d8947421010821dd8f3f7046ef0eccd5c27602c7505a5749c1090a0fe7435b",
    }[sys.platform]
    fast_hash = {
        "linux": "c97fda7d817a32aad65ce77f5043a51410c5893e6bab8e746a23f68c8e483774",
        "win32": "387b1ef12b70d4df0984846b753fbcceb1b7d079256e75479810b6a15d668b70",
        "darwin": "76ce19673caf9532d68730c7f83bfe8e6f521cc001c2d43373f9c4f33c925037",
    }[sys.platform]

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

    def test_stringify_numpy_fast(self):
        self.assertEqual(self.fast_hash, stable_hash(self.data))

    def test_stringify_torch(self):
        self.assertEqual(
            self.slow_hash,
            stable_hash(torch.tensor(self.data), fast_bytes=False),
        )

    def test_stringify_torch_fast(self):
        self.assertEqual(
            self.fast_hash,
            stable_hash(torch.tensor(self.data)),
        )

    def test_stringify_pandas(self):
        frame = pd.DataFrame(
            {
                "hi": [1, 2, 3],
                "bye": np.random.RandomState(0).randn(3),
                "hello": ["a", "b", "c"],
                "nested": list(np.random.RandomState(5).rand(3, 10)),
            },
            index=[None, "a", "b"],
        )
        self.assertEqual(
            "56db9e9bdc460416bf38da8e7f20610a0f24e56e66220ed486e20278754bcf28",
            stable_hash(frame),
        )
        frame.index = ["None", "a", "b"]
        self.assertEqual(
            "4910bc9c2474a409127d88a7ddb279b34559bae5114da65f419d4eeaa622fa97",
            stable_hash(frame),
        )
        frame = frame[["bye", "nested", "hello", "hi"]]
        self.assertEqual(
            "945c95c1f21efc1185ee4e4bcf3a24263881bc16564ec89ab7bb3a5d313455cb",
            stable_hash(frame),
        )
