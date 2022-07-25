import math
from textwrap import dedent

from scdil import dumps


def test_human_dump_simple() -> None:
    assert dumps(None) == "null"
    assert dumps(True) == "true"
    assert dumps(False) == "false"
    assert dumps(-math.inf) == "-inf"
    assert dumps(math.inf) == "inf"
    assert dumps(math.nan) == "nan"
    assert dumps(-10) == "-10"
    assert dumps(1e8) == "100000000.0"
    assert dumps(math.pi).startswith("3.141592")


def test_mapping_in_mapping() -> None:
    assert dumps({"a": 1, "b": {"c": 1}}) == dedent(
        """\
        a: 1
        b:
          c: 1
        """
    )


def test_mapping_in_sequence() -> None:
    assert dumps([{"a": 1}, {"b": 2}]) == dedent(
        """\
    -
      a: 1
    -
      b: 2
    """
    )
