import sys
import unittest

import numpy as np
import torch
from parameterized import parameterized_class
from torch import nn

from permacache import stable_hash

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

    def test_module_legacy_hash_regression_test(self):
        a2 = construct_with_seed(lambda: A(2), 1)
        a2_2 = construct_with_seed(lambda: A(2), 2)
        a3 = construct_with_seed(lambda: A(3), 1)
        b = construct_with_seed(B, 1)
        self.assertEqual(
            stable_hash(a2),
            "b4cf9ada8cfcce89dffaece16ac1934874ddf1046f59adc3c46bdb5fe249212d",
        )
        self.assertEqual(
            stable_hash(a2_2),
            "1f83444d2c69e9232240593cd5d4eaf956406df71cf8bc303309f80c1e1c11e0",
        )
        self.assertEqual(
            stable_hash(a3),
            "9e287d6ef5155d009bc32412beec66c0c4da6ac743d8272a12769c57478f9eac",
        )
        self.assertEqual(
            stable_hash(b),
            "68da0f08df42b89816cd09338f82a15a249775e832b461c8baa07a598a7e0513",
        )
        common_hash = "e026af439414722f25d8d9fac7b4df9996a9112620af64201a2d3abd4dc16574"
        self.assertEqual(stable_hash(Container(a2)), common_hash)
        self.assertEqual(stable_hash(Container(a3)), common_hash)
        self.assertEqual(stable_hash(Container(b)), common_hash)
        self.assertEqual(
            stable_hash(Container(a2_2)),
            "c7b97db9fa42363efa644b809391e2b2b086b2e4d6a820e56e29cd5b33c9f3f2",
        )
