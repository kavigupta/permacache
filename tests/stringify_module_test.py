import contextlib
import sys
import unittest

import numpy as np
import torch
from parameterized import parameterized, parameterized_class
from torch import nn

from permacache import stable_hash
from permacache.hash import valid_versions

NUMPY_VERSION = np.version.version.split(".", maxsplit=1)[0]


class A(nn.Module):
    def __init__(self, x):
        super().__init__()
        self.a = nn.Linear(10, 10)
        self.x = x

    def forward(self, x):
        return self.a(x) + self.x


class B(nn.Module):
    def __init__(self):
        super().__init__()
        self.a = nn.Linear(10, 10)

    def forward(self, x):
        return self.a(x)


class C(nn.Module):
    def __init__(self, x):
        super().__init__()
        self.a = nn.Linear(10, 10)
        self.x = x

    def forward(self, x):
        return self.a(x) + self.x


class Container(nn.Module):
    def __init__(self, a):
        super().__init__()
        self.u = a

    def forward(self, x):
        return self.u(x) * 2


# we just do this for one version of numpy and for linux. cross-platform and cross-numpy-version
# tests are in stringify_test.py

abc = [1] if sys.platform == "linux" and NUMPY_VERSION == "2" else []


def construct_with_seed(constructor, seed):
    torch.manual_seed(seed)
    return constructor()


@parameterized_class([{"abc": s} for s in abc])
class StringifyModuleTest(unittest.TestCase):

    @parameterized.expand([(None,), (1,)])
    def test_module_legacy_hash_regression_test(self, version):
        a2 = construct_with_seed(lambda: A(2), 1)
        a2_2 = construct_with_seed(lambda: A(2), 2)
        a3 = construct_with_seed(lambda: A(3), 1)
        b = construct_with_seed(B, 1)
        ctx = (
            self.assertWarns(FutureWarning)
            if version is None
            else contextlib.nullcontext()
        )
        with ctx:
            self.assertEqual(
                stable_hash(a2, version=version),
                "b4cf9ada8cfcce89dffaece16ac1934874ddf1046f59adc3c46bdb5fe249212d",
            )
            self.assertEqual(
                stable_hash(a2_2, version=version),
                "1f83444d2c69e9232240593cd5d4eaf956406df71cf8bc303309f80c1e1c11e0",
            )
            self.assertEqual(
                stable_hash(a3, version=version),
                "9e287d6ef5155d009bc32412beec66c0c4da6ac743d8272a12769c57478f9eac",
            )
            self.assertEqual(
                stable_hash(b, version=version),
                "68da0f08df42b89816cd09338f82a15a249775e832b461c8baa07a598a7e0513",
            )
            common_hash = (
                "e026af439414722f25d8d9fac7b4df9996a9112620af64201a2d3abd4dc16574"
            )
            self.assertEqual(stable_hash(Container(a2), version=version), common_hash)
            self.assertEqual(stable_hash(Container(a3), version=version), common_hash)
            self.assertEqual(stable_hash(Container(b), version=version), common_hash)
            self.assertEqual(
                stable_hash(Container(a2_2), version=version),
                "c7b97db9fa42363efa644b809391e2b2b086b2e4d6a820e56e29cd5b33c9f3f2",
            )

    @parameterized.expand(
        [(vers,) for vers in valid_versions if vers is not None and vers >= 2]
    )
    def test_module_hash_regression_test(self, version):
        a2 = construct_with_seed(lambda: A(2), 1)
        a2_2 = construct_with_seed(lambda: A(2), 2)
        a3 = construct_with_seed(lambda: A(3), 1)
        b = construct_with_seed(B, 1)
        c2 = construct_with_seed(lambda: C(2), 1)
        self.assertEqual(
            stable_hash(a2, version=version),
            "084d34856445ed411c91b0d27c3e2405d3f2a48178739ca5efa979bbe03e69b2",
        )
        self.assertEqual(
            stable_hash(a2_2, version=version),
            "e990be249dc5fcdc7fbe78d65b631cd18bc24f5127984fa359110374d224e6b0",
        )
        self.assertEqual(
            stable_hash(a3, version=version),
            "24e0a3d5335e394ff9a1e933b9e7302b5dd2c34c571baf360aaaa5da02fb7f99",
        )
        self.assertEqual(
            stable_hash(b, version=version),
            "16df7d27339b6fc8665a1319870c5fccb87e34c35523afb591709ed8821a2f59",
        )
        self.assertEqual(
            stable_hash(Container(a2), version=version),
            "52c93a8d4c98c1a409eb16c4364474c34c512e881b12546fa22acd2fb908f165",
        )
        self.assertEqual(
            stable_hash(Container(a3), version=version),
            "a17cac5329e120feda1025947199dc28f3927ae9e8cb86797d200483980ac3a8",
        )
        self.assertEqual(
            stable_hash(Container(b), version=version),
            "af36fa8427d29013da1e6634ec66dcf250a29a0f737c06c843c18c5696380b04",
        )
        self.assertEqual(
            stable_hash(Container(c2), version=version),
            "6ee17c5792eb1d52719f9e0f85102ed5c1255a9bb23dd68df14f38b07024e120",
        )
        self.assertEqual(
            len(
                {
                    stable_hash(a2, version=version),
                    stable_hash(a3, version=version),
                    stable_hash(b, version=version),
                    stable_hash(c2, version=version),
                    stable_hash(Container(a2), version=version),
                    stable_hash(Container(a3), version=version),
                    stable_hash(Container(b), version=version),
                    stable_hash(Container(c2), version=version),
                }
            ),
            8,
        )
        self.assertEqual(
            stable_hash(Container(a2_2), version=version),
            "9a032bb2785dcd1489991851936214bc77047c2b09873489bf0e19252246e1b5",
        )
