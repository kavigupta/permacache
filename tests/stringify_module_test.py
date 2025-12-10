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
        # with self.assertWarns(DeprecationWarning):
        ctx = (
            self.assertWarns(DeprecationWarning)
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
            "f7de7326df407c1119472c468eae7964922f267da301c9419baeb59d7094a9cd",
        )
        self.assertEqual(
            stable_hash(a2_2, version=version),
            "3b17039cffed242d422614b27db0b4bbb0c8d2ed2c489d4fd7485a9c53fd93dc",
        )
        self.assertEqual(
            stable_hash(a3, version=version),
            "66a331418a5d0673dbe8ebcf020baf18b3c42498b46597ed9261f6082239881d",
        )
        self.assertEqual(
            stable_hash(b, version=version),
            "393a568be899bcd47becca86923703a9de3db2d83d6367242571d6b802484e90",
        )
        self.assertEqual(
            stable_hash(Container(a2), version=version),
            "adb943bbbf513b12e958976bfb2b400ef4a7f2fe7debb45d424b5b09b27086c5",
        )
        self.assertEqual(
            stable_hash(Container(a3), version=version),
            "a5c4ff1d253358aca309d9a7d85c2e65375a2d57430c4fd5f06979c6ae11538d",
        )
        self.assertEqual(
            stable_hash(Container(b), version=version),
            "273817633d4d59481b8ed87c6579cd8a2e91ff44935e6fe6e3394da28bce6d19",
        )
        self.assertEqual(
            stable_hash(Container(c2), version=version),
            "da340c73bb161e048c7e55c072b5a712f1c2c55963f8f20eb695a2859be35858",
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
            "318ddd93712275a4120b3f993346a760e1dcdca07f18c456bc0a9b661ed0046e",
        )
