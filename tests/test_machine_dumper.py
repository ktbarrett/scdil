import math

import pytest

import scdil
from scdil import FrozenDict


def dumps(value: scdil.Value) -> str:
    return scdil.dumps(value, for_humans=False)


def test_scalar() -> None:
    assert dumps(None) == "null"
    assert dumps(True) == "true"
    assert dumps(False) == "false"
    assert dumps(-math.inf) == "-inf"
    assert dumps(math.inf) == "inf"
    assert dumps(math.nan) == "nan"
    assert dumps(-10) == "-10"
    assert dumps(1e8) == "100000000.0"
    assert dumps(math.pi).startswith("3.141592")
    assert dumps("") == '""'
    assert (
        dumps("ab℞⽢⯫Ⳝ\x00\u007e\U00010111\n\r\t\\\"'")
        == '"ab℞⽢⯫Ⳝ\\x00~𐄑\\n\\r\\t\\\\\\"\'"'
    )


def test_empty_sequence() -> None:
    assert dumps([]) == "[]"


def test_empty_mapping() -> None:
    assert dumps({}) == "{}"


def test_simple_sequence() -> None:
    assert dumps([1.0, None, False]) == "[1.0,null,false]"


def test_simple_mapping() -> None:
    assert dumps({"a": 1, False: None}) == '{"a":1,false:null}'


def test_sequence_elem_is_sequence() -> None:
    assert dumps([[1, 2, 3], 4]) == "[[1,2,3],4]"


def test_sequence_elem_is_mapping() -> None:
    assert dumps([{"a": 1, None: -17689.0}]) == '[{"a":1,null:-17689.0}]'


def test_mapping_value_is_sequence() -> None:
    assert dumps({1: [1, 2, 3]}) == "{1:[1,2,3]}"


def test_mapping_value_is_mapping() -> None:
    assert dumps({None: {"a": 1}}) == '{null:{"a":1}}'


def test_mapping_key_is_sequence() -> None:
    assert (
        dumps({(1, 2): False, "b": -1e-9}) == '{[1,2]:false,"b":-1e-09}'
    )  # odd it adds a 0 there... but it is valid


def test_mapping_key_is_mapping() -> None:
    assert dumps({FrozenDict({"a": None, False: 1}): 0}) == '{{"a":null,false:1}:0}'


def test_unsuspported_type() -> None:
    with pytest.raises(TypeError):
        assert dumps(object())
    with pytest.raises(TypeError):
        assert dumps(set())


def test_recursive_obj() -> None:
    d = {}
    d["a"] = d
    with pytest.raises(ValueError):
        dumps(d)
    d = []
    d.append(d)
    with pytest.raises(ValueError):
        dumps(d)
