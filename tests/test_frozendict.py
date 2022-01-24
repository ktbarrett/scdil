import sys

import pytest

from scdil.frozendict import FrozenDict


def test_construct() -> None:
    a = FrozenDict[int, str]()
    assert len(a) == 0

    b = FrozenDict(a=1, b="wew")
    assert b["a"] == 1
    assert b["b"] == "wew"

    c_data = [(None, -1.0), ("n", 1), (9, False)]
    c = FrozenDict(c_data)
    assert list(c.items()) == c_data

    d_data = {"a": 1, "1": False}
    d = FrozenDict(d_data)
    assert dict(**d) == d_data

    keys = ["1", 1, 1.0]
    e = FrozenDict.fromkeys(keys, "one")
    assert set(e.keys()) == set(keys)
    assert all(value == "one" for value in e.values())

    f = d.copy()
    assert f == d

    with pytest.raises(TypeError):
        FrozenDict(7)  # type: ignore


def test_immutable() -> None:
    f = FrozenDict[str, int](a=1)
    with pytest.raises(TypeError):
        f[0] = 6  # type: ignore
    with pytest.raises(TypeError):
        f["a"] = 2  # type: ignore


def test_iterators() -> None:
    keys = {1, "2", False}
    values = {None, 2.0, object()}
    items = set(zip(keys, values))

    f = FrozenDict(items)
    assert set(f.keys()) == keys
    assert set(f.values()) == values
    assert set(f.items()) == items
    assert set(f) == keys
    assert set(reversed(f)) == keys


def test_hashable() -> None:
    a = {
        FrozenDict(a=1),
        FrozenDict(a=1),
    }
    assert len(a) == 1
    a.add(FrozenDict(b=2))
    assert len(a) == 2


def test_equals() -> None:
    a = FrozenDict(a=1)
    assert a == FrozenDict(a=1)
    assert a != FrozenDict(a=1, b=9)
    assert FrozenDict() != 0
    assert 0 != FrozenDict()


def test_repr() -> None:
    a = FrozenDict({"a": 1, 1.0: None, False: "True"})
    assert eval(repr(a)) == a


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_union() -> None:
    a = FrozenDict(a=1, b=2)
    b = FrozenDict(b=3, c=3)
    assert a | b == FrozenDict(a=1, b=3, c=3)
    assert b | a == FrozenDict(a=1, b=2, c=3)
    assert a | dict(a=6) == FrozenDict(a=6, b=2)
    assert dict(a=6) | a == FrozenDict(a=1, b=2)
    with pytest.raises(TypeError):
        a | {1, 2, 3}  # type: ignore
    with pytest.raises(TypeError):
        123 | a  # type: ignore
