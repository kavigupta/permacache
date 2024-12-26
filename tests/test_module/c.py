from dataclasses import dataclass

import attr

from permacache import migrated_attrs


@attr.s
class A:
    x = attr.ib()
    y = attr.ib()
    z = attr.ib()


@attr.dataclass
class B:
    x: int
    y: str
    z: float


@dataclass
class C:
    x: int
    y: str
    z: float


@dataclass
@migrated_attrs
class D:
    x: int
    y: str
    z: float
